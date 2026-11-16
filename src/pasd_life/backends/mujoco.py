"""Optional MuJoCo backend (Linux/headless). Contract: docs/01 section 9 / docs/08 section 5.

Loads the AgileX PiPER MJCF (configs/mujoco/piper.xml) and maps the five whitelisted
primitives to MuJoCo. Joint-space control; Cartesian IK is deferred. Friction / grip
calibration is still pending (configs/calibration.yaml), so Gate2 success rates are
NOT yet physically calibrated.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BackendUnavailable

GRIPPER_HALF_RANGE = 0.035   # metres, per finger (joint7/8 range)
SIM_STEPS = 50               # physics steps per primitive call


def _require_model() -> Path:
    # repo_root = parents[3] of src/pasd_life/backends/mujoco.py
    root = Path(__file__).resolve().parents[3]
    model = root / "configs" / "mujoco" / "piper.xml"
    if not model.is_file():
        raise BackendUnavailable(
            "MuJoCo model not found: configs/mujoco/piper.xml. "
            "Provide a PiPER MJCF before running Gate2 in simulation."
        )
    return model


class MuJoCoBackend:
    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = model_path or _require_model()
        try:
            import mujoco
        except ImportError as exc:
            raise BackendUnavailable(
                "mujoco is not installed. On Linux: pip install -e '.[sim]' "
                "(headless needs libgl1 / libosmesa6)."
            ) from exc
        self._mj = mujoco
        self._model = mujoco.MjModel.from_xml_path(str(self.model_path))
        self._data = mujoco.MjData(self._model)
        mujoco.mj_resetData(self._model, self._data)
        self._arm_acts = [mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"joint{i}")
                          for i in range(1, 7)]
        self._gripper_act = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_ACTUATOR, "gripper")
        self._gripper_joint = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_JOINT, "joint7")
        self._eef_speed = 0.0

    def _step(self, n: int = SIM_STEPS) -> None:
        for _ in range(n):
            self._mj.mj_step(self._model, self._data)

    def observation(self) -> dict:
        # Only real-observable quantities; no simulation ground truth.
        return {
            "joint_state": [float(self._data.qpos[i]) for i in range(6)],
            "gripper_width": float(self._data.qpos[self._gripper_joint]) * 2.0,
            "pose_confidence": 1.0,
            "eef_speed": self._eef_speed,
        }

    def step(self, name: str, **kwargs: Any) -> dict | None:
        if name == "get_observation":
            return self.observation()
        if name == "open_gripper":
            self._data.ctrl[self._gripper_act] = 0.0
            self._step()
            return {"gripper_open": True, "gripper_width": 0.0}
        if name == "close_gripper":
            width = float(kwargs.get("width", 0.0))
            half = max(0.0, min(GRIPPER_HALF_RANGE, width / 2.0))
            self._data.ctrl[self._gripper_act] = half
            self._step()
            return {"gripper_open": False, "gripper_width": half * 2.0}
        if name == "move_to_pose":
            pose = kwargs.get("pose") or {}
            self._eef_speed = float(kwargs.get("speed", 0.1))
            q = pose.get("q") if isinstance(pose, dict) else None
            if q is not None:
                for i, act in enumerate(self._arm_acts):
                    self._data.ctrl[act] = float(q[i])
                self._step()
            return {"reached": True, "eef_speed": self._eef_speed}
        if name == "solve_ik":
            # Full Cartesian IK is deferred; joint-space control is used for now.
            return None
        raise BackendUnavailable(f"unsupported primitive: {name}")

    def estop(self) -> None:
        # Control-layer e-stop: zero all actuator commands (never routed through the LLM).
        self._data.ctrl[:] = 0.0


class MuJoCoSimRunner:
    """Gate2 grasp simulation over the MuJoCo scene (WIP — needs visual tuning).

    Loads configs/mujoco/scene_grasp.xml (arm + table + slender rod) and runs a
    grasp attempt; success = the target rod is still held after lifting. The
    grasp geometry, IK convergence and friction are NOT yet tuned for the
    GRASP_SLIP physics — verify on a display before trusting the results.
    """

    def __init__(self, scene_path: Path | None = None) -> None:
        root = Path(__file__).resolve().parents[3]
        self._scene = scene_path or root / "configs" / "mujoco" / "scene_grasp.xml"
        if not Path(self._scene).is_file():
            raise BackendUnavailable(f"scene not found: {self._scene}")
        try:
            import mujoco
        except ImportError as exc:
            raise BackendUnavailable("mujoco is not installed: pip install -e '.[sim]'") from exc
        self._mj = mujoco
        self._model = mujoco.MjModel.from_xml_path(str(self._scene))
        self._data = mujoco.MjData(self._model)
        self._home = [0.0, 1.57, -1.3485, 0.0, 0.0, 0.0, 0.0, 0.0]
        self._gripper_act = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_ACTUATOR, "gripper")
        self._rod = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_BODY, "rod")

    def run(self, skill) -> bool:
        """Run one grasp attempt and report whether the rod is held (physics-based).

        WIP: the rod placement / grasp pose / friction need visual tuning; this is
        the mechanism, not a calibrated GRASP_SLIP detector.
        """
        mj, model, d = self._mj, self._model, self._data
        mj.mj_resetData(model, d)
        d.qpos[:8] = self._home
        d.qvel[:] = 0.0
        # open the gripper, then close to the rod width, then lift
        d.ctrl[self._gripper_act] = 0.035
        for _ in range(200):
            mj.mj_step(model, d)
        d.ctrl[self._gripper_act] = 0.008
        for _ in range(300):
            mj.mj_step(model, d)
        # lift: raise the elbow (joint2) a little
        arm_act1 = mj.mj_name2id(model, mj.mjtObj.mjOBJ_ACTUATOR, "joint2")
        d.ctrl[arm_act1] = self._home[1] + 0.25
        for _ in range(500):
            mj.mj_step(model, d)
        return float(d.xpos[self._rod][2]) > 0.34
