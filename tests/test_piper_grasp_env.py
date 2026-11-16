"""PiPER grasp env: reset / rod position / grasp (headless; render may be None)."""
import unittest

import numpy as np

from src.pasd_life.piper_grasp_env import PiperGraspEnv


class TestPiperGraspEnv(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls._env = PiperGraspEnv()
        except Exception as exc:  # noqa: BLE001
            raise unittest.SkipTest(f"mujoco/model unavailable: {exc}")

    def test_reset_and_rod_position(self):
        self._env.reset()
        pos = self._env.rod_position()
        self.assertEqual(pos.shape, (3,))
        self.assertGreater(pos[2], 0.2)  # rod above the table at reset

    def test_grasp_returns_bool(self):
        self._env.reset()
        target = self._env.rod_position() + np.array([0.0, 0.0, 0.02])
        result = self._env.grasp(target, width=0.008)
        self.assertIsInstance(result, bool)

    def test_render_graceful(self):
        self._env.reset()
        out = self._env.render()
        # headless: either None (no GL) or a dict with img + depth
        self.assertTrue(out is None or set(out) == {"img", "depth"})


if __name__ == "__main__":
    unittest.main()
