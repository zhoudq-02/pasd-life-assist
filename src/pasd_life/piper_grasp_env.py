"""PiPER grasp environment: MuJoCo scene + PiperKinematics + RGB-D render + grasp.

Pure mujoco + numpy (no roboticstoolbox). RGB-D rendering degrades gracefully when
no display / GL is available (returns None instead of crashing).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .piper_kinematics import HOME_Q, PiperKinematics

HOME_QPOS = [0.0, 1.57, -1.3485, 0.0, 0.0, 0.0, 0.0, 0.0]  # + joint7/8


class PiperGraspEnv:
    def __init__(self, scene_path: Path | str | None = None,
                 height: int = 480, width: int = 640) -> None:
        import mujoco

        root = Path(__file__).resolve().parents[2]  # src/pasd_life -> repo root
        self._scene = Path(scene_path) if scene_path else root / "configs" / "mujoco" / "scene_grasp.xml"
        self._mj = mujoco
        self._model = mujoco.MjModel.from_xml_path(str(self._scene))
        self._data = mujoco.MjData(self._model)
        self._kin = PiperKinematics()

        self._gripper_act = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_ACTUATOR, "gripper")
        self._arm_acts = [mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"joint{i}")
                          for i in range(1, 7)]
        self._rod = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_BODY, "rod")

        self._height, self._width = height, width
        self._renderer = None
        self._depth_renderer = None
        self._cam = mujoco.MjvCamera()
        self._cam.lookat[:] = [0.5, 0.0, 0.3]
        self._cam.distance = 1.2
        self._cam.azimuth = 180.0
        self._cam.elevation = -25.0

    # ---- lifecycle ---------------------------------------------------------
    def reset(self) -> None:
        self._mj.mj_resetData(self._model, self._data)
        self._data.qpos[:8] = HOME_QPOS
        self._data.qvel[:] = 0.0
        for i, act in enumerate(self._arm_acts):
            self._data.ctrl[act] = HOME_QPOS[i]
        self._data.ctrl[self._gripper_act] = HOME_QPOS[6]
        self._mj.mj_forward(self._model, self._data)

    def step(self, n: int = 1) -> None:
        for _ in range(n):
            self._mj.mj_step(self._model, self._data)

    # ---- rendering (graceful) ---------------------------------------------
    def _init_renderer(self):
        try:
            self._renderer = self._mj.Renderer(self._model, self._height, self._width)
            self._depth_renderer = self._mj.Renderer(self._model, self._height, self._width)
            self._depth_renderer.enable_depth_rendering()
        except Exception:  # noqa: BLE001 — no GL on headless hosts
            self._renderer = None
            self._depth_renderer = None

    def render(self) -> dict | None:
        """Return {'img': RGB, 'depth': depth} or None when GL is unavailable."""
        if self._renderer is None:
            self._init_renderer()
        if self._renderer is None:
            return None
        self._renderer.update_scene(self._data, self._cam)
        self._depth_renderer.update_scene(self._data, self._cam)
        return {"img": self._renderer.render(), "depth": self._depth_renderer.render()}

    # ---- grasp -------------------------------------------------------------
    def rod_position(self) -> np.ndarray:
        return self._data.xpos[self._rod].copy()

    def grasp(self, target, width: float = 0.008, lift: float = 0.25) -> bool:
        """IK the gripper to `target` (xyz), close the gripper, lift, and report held.

        Returns True if the rod is still held (z > 0.34) after the lift — the
        physics-based grasp success signal (WIP: friction/grasp pose need tuning).
        """
        q = self._kin.ikine(target)
        if q is None:
            return False
        self._data.qpos[:6] = q
        for i, act in enumerate(self._arm_acts):
            self._data.ctrl[act] = q[i]
        self.step(200)
        # close the gripper around the target width
        self._data.ctrl[self._gripper_act] = max(0.0, min(0.035, width / 2.0))
        self.step(300)
        # lift: raise the elbow
        self._data.ctrl[self._arm_acts[1]] = self._data.qpos[1] + lift
        self.step(500)
        return float(self._data.xpos[self._rod][2]) > 0.34
