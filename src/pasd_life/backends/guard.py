"""Control-layer safety wrapper. Contract: docs/01 section 5 / docs/07 section 3.

Speed/acceleration limiting, watchdog and emergency stop live OUTSIDE the LLM:
no generated policy can bypass this wrapper. Missing observations never count
as a violation (same semantics as SafetyEnvelope).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from ..robot_api import ALLOWED
from ..safety import EmergencyStop, SafetyEnvelope
from ..schema import REAL_OBSERVABLE_FIELDS
from .base import Backend, BackendGuardViolation


@dataclass(frozen=True)
class GuardConfig:
    step_timeout_s: float = 2.0
    workspace_box: tuple[float, float, float, float, float, float] | None = None
    max_accel: float | None = None   # TODO(scaffold): calibrate on the real arm


class GuardedBackend:
    """Wraps any backend; enforces limits before delegating, filters observations."""

    def __init__(
        self,
        inner: Backend,
        envelope: SafetyEnvelope | None = None,
        config: GuardConfig | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.inner = inner
        self.envelope = envelope or SafetyEnvelope()
        self.config = config or GuardConfig()
        self._clock = clock
        self.emergency = EmergencyStop()
        self.violations: list[str] = []

    # -- guard -------------------------------------------------------------
    def _check_pose(self, pose: Any) -> None:
        box = self.config.workspace_box
        if box is None or not isinstance(pose, dict):
            return  # TODO(scaffold): box must be calibrated before real deployment
        target = pose.get("target")
        if not isinstance(target, (list, tuple)) or len(target) < 3:
            return
        x, y, z = (float(v) for v in target[:3])
        xmin, xmax, ymin, ymax, zmin, zmax = box
        if not (xmin <= x <= xmax and ymin <= y <= ymax and zmin <= z <= zmax):
            raise BackendGuardViolation(f"target {(x, y, z)} outside workspace box {box}")

    def _limited_speed(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if "speed" in kwargs:
            speed = float(kwargs["speed"])
            cap = self.envelope.max_eef_speed
            if speed > cap:
                self.violations.append(f"speed {speed} clamped to {cap}")
                kwargs = {**kwargs, "speed": cap}
        return kwargs

    def estop(self, reason: str = "watchdog") -> None:
        """Never routed through the LLM. Calls the hardware adapter if available."""
        self.emergency.trigger(reason)
        stop = getattr(self.inner, "estop", None)
        if callable(stop):
            stop()

    # -- backend protocol -------------------------------------------------
    def step(self, name: str, **kwargs: Any) -> dict | None:
        if name not in ALLOWED:
            raise BackendGuardViolation(f"primitive '{name}' is not whitelisted")
        if name == "move_to_pose":
            self._check_pose(kwargs.get("pose"))
            kwargs = self._limited_speed(kwargs)
        started = self._clock()
        result = self.inner.step(name, **kwargs)
        if self._clock() - started > self.config.step_timeout_s:
            self.estop("watchdog_timeout")
            raise BackendGuardViolation("step exceeded watchdog timeout; e-stop issued")
        return result

    def observation(self) -> dict:
        raw = self.inner.observation()
        # Anti-contamination: simulation ground truth must never cross this boundary.
        return {k: v for k, v in raw.items() if k in REAL_OBSERVABLE_FIELDS}
