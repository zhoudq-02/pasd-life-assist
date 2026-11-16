"""MuJoCo backend: load the PiPER MJCF, control joints + gripper, read state."""
import unittest

from src.pasd_life.backends.mujoco import MuJoCoBackend
from src.pasd_life.backends.base import BackendUnavailable


class TestMuJoCoBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls._backend = MuJoCoBackend()
        except BackendUnavailable as exc:
            raise unittest.SkipTest(f"mujoco/model unavailable: {exc}")

    def test_observation_has_joint_state(self):
        obs = self._backend.observation()
        self.assertEqual(len(obs["joint_state"]), 6)
        self.assertIn("gripper_width", obs)

    def test_gripper_open_close(self):
        self._backend.step("open_gripper")
        out = self._backend.step("close_gripper", width=0.022)
        self.assertFalse(out["gripper_open"])
        self.assertLessEqual(self._backend.observation()["gripper_width"], 0.022 + 1e-6)

    def test_move_to_pose_joint_space(self):
        out = self._backend.step("move_to_pose",
                                 pose={"q": [0.1, 0.2, -0.3, 0.1, 0.0, 0.0]}, speed=0.1)
        self.assertTrue(out["reached"])

    def test_solve_ik_returns_none_for_now(self):
        self.assertIsNone(self._backend.step("solve_ik", target_pose=[0.3, 0.0, 0.15]))


if __name__ == "__main__":
    unittest.main()
