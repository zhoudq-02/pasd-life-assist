"""AgileX PiPER real-arm adapter (Linux/CAN). Contract: docs/01 section 9 / docs/08 section 6.

IMPORTANT: the concrete `piper_sdk` call names and unit conventions are NOT
verified against a live arm in this repository. `PiperSDKAdapter` therefore fails
loudly with a checklist instead of guessing an API and moving hardware. Supply a
site-specific adapter via `PASD_ADAPTER=null` (dry-run) or replace the five
methods below after checking the SDK manual on the target machine.
"""
from __future__ import annotations

from typing import Any

from ..schema import REAL_OBSERVABLE_FIELDS
from .base import BackendUnavailable
from .settings_adapter import AdapterSettings


class NullAdapter:
    """Connectivity dry-run: exercises the whole stack without moving anything."""

    name = "null"

    def __init__(self, cfg: AdapterSettings) -> None:
        self.cfg = cfg
        self.calls: list[tuple[str, dict]] = []
        self.gripper_open = True

    def connect(self) -> None:
        self.calls.append(("connect", {"can": self.cfg.can_interface,
                                       "bitrate": self.cfg.can_bitrate}))

    def observe(self) -> dict:
        # Only real-observable fields; unknown sensors are explicitly not invented.
        return {k: None for k in sorted(REAL_OBSERVABLE_FIELDS)}

    def move(self, pose: Any, speed: float) -> dict:
        self.calls.append(("move", {"pose": pose, "speed": speed}))
        return {"reached": True, "eef_speed": speed, "dry_run": True}

    def gripper(self, open_: bool, width_m: float) -> dict:
        self.gripper_open = open_
        self.calls.append(("gripper", {"open": open_, "width_m": width_m}))
        return {"gripper_open": open_, "gripper_width": width_m, "dry_run": True}

    def ik(self, target_pose: Any) -> dict | None:
        self.calls.append(("ik", {"target_pose": target_pose}))
        return {"q": [0.0] * 6, "dry_run": True}

    def stop(self) -> None:
        self.calls.append(("stop", {}))


class PiperSDKAdapter(NullAdapter):
    """TODO(verify-sdk-api): replace the five methods with real `piper_sdk` calls."""

    name = "sdk"

    def connect(self) -> None:
        try:
            import piper_sdk  # noqa: F401  # type: ignore[import-not-found]
        except ImportError as exc:
            raise BackendUnavailable(
                "piper_sdk is not installed. On Linux: pip install -e '.[robot]'; "
                "then check CAN with deploy/setup_can.sh and the udev rule."
            ) from exc
        raise BackendUnavailable(
            "piper_sdk is present but NOT yet verified on a live arm. SDK source "
            "(v0.6.1) gives: C_PiperInterface_V2.ConnectPort() / EnablePiper() / "
            "JointCtrl (0.001 deg) / GripperCtrl (0.001 mm) / EmergencyStop(0x01) — "
            "see docs/09 for the full 6-item checklist and the minimal adapter mapping. "
            "Verify each on the CAN arm before wiring PiperSDKAdapter (SI-unit contract)."
        )


def make_adapter(cfg: AdapterSettings):
    return NullAdapter(cfg) if cfg.adapter == "null" else PiperSDKAdapter(cfg)


class PiperCANBackend:
    """Five-primitive backend over an injected adapter. Never touches CAN itself."""

    def __init__(self, cfg: AdapterSettings, adapter=None) -> None:
        self.cfg = cfg
        self.adapter = adapter or make_adapter(cfg)
        self.adapter.connect()

    @property
    def dry_run(self) -> bool:
        return getattr(self.adapter, "name", "") == "null"

    def observation(self) -> dict:
        raw = self.adapter.observe()
        return {k: v for k, v in raw.items() if k in REAL_OBSERVABLE_FIELDS}

    def step(self, name: str, **kwargs: Any) -> dict | None:
        if name == "get_observation":
            return self.observation()
        if name == "move_to_pose":
            return self.adapter.move(kwargs.get("pose"), float(kwargs.get("speed", 0.1)))
        if name == "open_gripper":
            return self.adapter.gripper(True, float(kwargs.get("width", 0.0)))
        if name == "close_gripper":
            return self.adapter.gripper(False, float(kwargs.get("width", 0.0)))
        if name == "solve_ik":
            return self.adapter.ik(kwargs.get("target_pose"))
        raise BackendUnavailable(f"unsupported primitive: {name}")

    def estop(self) -> None:
        self.adapter.stop()
