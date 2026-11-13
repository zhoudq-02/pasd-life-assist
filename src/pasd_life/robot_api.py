"""Whitelisted RobotAPI (5 primitives) + MockPiPER backend. Contract: docs/01 section 3."""
from __future__ import annotations

from typing import Any

from .config import ASPECT_RATIO_SLIP, MAX_GRIPPER_WIDTH
from .schema import PiPERError, REAL_OBSERVABLE_FIELDS

ALLOWED = frozenset({
    "move_to_pose", "open_gripper", "close_gripper", "get_observation", "solve_ik",
})


class WhitelistViolation(RuntimeError):
    """Raised before execution whenever a non-whitelisted primitive is requested."""


class MockPiPER:
    """Standard-library backend encoding the PiPER physical semantics.

    TODO(scaffold): MuJoCoBackend and RealPiPERBackend must implement the same
    `step(name, **kwargs)` / `observation()` interface, with optional imports
    guarded by try/except ImportError.
    """

    def __init__(self, scene: dict | None = None) -> None:
        self.scene: dict[str, Any] = dict(scene or {})
        self.calls: list[tuple[str, dict]] = []
        self.last_approach: str = str(self.scene.get("approach", "top"))
        self.gripper_open = True

    def observation(self) -> dict:
        # Anti-contamination: simulation ground truth never leaves this boundary.
        return {k: v for k, v in self.scene.items() if k in REAL_OBSERVABLE_FIELDS}

    def step(self, name: str, **kwargs: Any) -> dict | None:
        self.calls.append((name, kwargs))
        if name == "get_observation":
            return self.observation()
        if name == "open_gripper":
            self.gripper_open = True
            return {"gripper_open": True}
        if name == "move_to_pose":
            pose = kwargs.get("pose") or {}
            if isinstance(pose, dict) and "approach" in pose:
                self.last_approach = str(pose["approach"])
            if not self.scene.get("ik_solvable", True):
                raise PiPERError("IK_UNREACHABLE", {}, "6-DoF arm has no null space")
            return {"reached": True, "eef_speed": float(kwargs.get("speed", 0.1))}
        if name == "solve_ik":
            if not self.scene.get("ik_solvable", True):
                return None
            return {"q": [0.0] * 6}
        if name == "close_gripper":
            width = float(kwargs.get("width", 0.0))
            target_width = float(self.scene.get("target_width", width))
            if target_width > MAX_GRIPPER_WIDTH:
                raise PiPERError(
                    "GRASP_IMPOSSIBLE", {"target_width": target_width},
                    "target width exceeds 70 mm gripper range",
                )
            aspect = float(self.scene.get("aspect_ratio", 1.0))
            if aspect > ASPECT_RATIO_SLIP and self.last_approach == "top":
                raise PiPERError(
                    "GRASP_SLIP", {"aspect_ratio": aspect},
                    "slender object with top approach slips",
                )
            self.gripper_open = False
            return {"gripper_open": False, "gripper_width": width, "grasp_ok": True}
        raise WhitelistViolation(f"unknown primitive: {name}")


class RobotAPI:
    def __init__(self, backend: Any) -> None:
        self.backend = backend
        self.call_log: list[tuple[str, dict]] = []

    def call(self, name: str, **kwargs: Any) -> Any:
        if name not in ALLOWED:
            raise WhitelistViolation(f"primitive '{name}' is not in the whitelist")
        self.call_log.append((name, kwargs))
        return self.backend.step(name, **kwargs)

    def move_to_pose(self, pose: Any, speed: float = 0.1) -> Any:
        return self.call("move_to_pose", pose=pose, speed=speed)

    def open_gripper(self) -> Any:
        return self.call("open_gripper")

    def close_gripper(self, width: float) -> Any:
        return self.call("close_gripper", width=width)  # width in metres

    def get_observation(self) -> dict:
        return self.call("get_observation")

    def solve_ik(self, target_pose: Any) -> Any:
        return self.call("solve_ik", target_pose=target_pose)
