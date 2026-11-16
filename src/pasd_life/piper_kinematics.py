"""PiPER kinematics: FK from the AgileX MJCF + numerical IK (Jacobian transpose).

Standalone — numpy + mujoco only (no roboticstoolbox). Maps a grasp position to the
6 arm joint angles and back, so GraspNet grasp poses can land on the PiPER arm.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

HOME_Q = np.array([0.0, 1.57, -1.3485, 0.0, 0.0, 0.0])


class PiperKinematics:
    def __init__(self, model_path: Path | str | None = None) -> None:
        import mujoco

        root = Path(__file__).resolve().parents[2]  # src/pasd_life -> repo root
        self._model_path = Path(model_path) if model_path else root / "configs" / "mujoco" / "piper.xml"
        self._mj = mujoco
        self._m = mujoco.MjModel.from_xml_path(str(self._model_path))
        self._d = mujoco.MjData(self._m)
        self._ee = mujoco.mj_name2id(self._m, mujoco.mjtObj.mjOBJ_BODY, "link7")
        self._jnt_range = self._m.jnt_range[:6].copy()  # (6, 2)

    @property
    def joint_limits(self) -> np.ndarray:
        return self._jnt_range.copy()

    def fkine(self, q) -> np.ndarray:
        """Forward kinematics: gripper (link7) position for joint angles q (rad)."""
        d = self._d
        d.qpos[:6] = q
        self._mj.mj_forward(self._m, d)
        return d.xpos[self._ee].copy()

    def _jacobian(self, q: np.ndarray) -> np.ndarray:
        m, d = self._m, self._d
        eps = 1e-3
        d.qpos[:6] = q
        self._mj.mj_forward(m, d)
        base = d.xpos[self._ee].copy()
        J = np.zeros((3, 6))
        for j in range(6):
            qp = q.copy()
            qp[j] += eps
            d.qpos[:6] = qp
            self._mj.mj_forward(m, d)
            J[:, j] = (d.xpos[self._ee] - base) / eps
        return J

    def ikine(self, target, q0=None, n_iter: int = 800, tol: float = 1e-3,
              lr: float = 0.4) -> np.ndarray | None:
        """Numerical IK (Jacobian transpose) to reach `target` (xyz), within joint limits.

        Returns the 6 arm joint angles (rad), or None if it does not converge.
        """
        m, d = self._m, self._d
        q = np.array(q0 if q0 is not None else HOME_Q, dtype=float)
        lo, hi = self._jnt_range[:, 0], self._jnt_range[:, 1]
        for _ in range(n_iter):
            d.qpos[:6] = q
            self._mj.mj_forward(m, d)
            e = np.asarray(target, dtype=float) - d.xpos[self._ee]
            if float(np.linalg.norm(e)) < tol:
                return q
            dq = lr * self._jacobian(q).T @ e
            q = np.clip(q + dq, lo, hi)
        return None
