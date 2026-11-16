"""PiPER kinematics: FK / numerical IK round-trip."""
import unittest

import numpy as np

from src.pasd_life.piper_kinematics import PiperKinematics
from src.pasd_life.backends.base import BackendUnavailable


class TestPiperKinematics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls._kin = PiperKinematics()
        except Exception as exc:  # noqa: BLE001 (mujoco/model absent)
            raise unittest.SkipTest(f"mujoco/model unavailable: {exc}")

    def test_fkine_home(self):
        pos = self._kin.fkine([0.0, 1.57, -1.3485, 0.0, 0.0, 0.0])
        self.assertEqual(pos.shape, (3,))
        self.assertAlmostEqual(pos[0], 0.50, delta=0.05)  # home gripper is around (0.50, 0, 0.36)

    def test_ikine_round_trip(self):
        target = self._kin.fkine([0.0, 1.57, -1.3485, 0.0, 0.0, 0.0]) + np.array([0.0, 0.0, -0.05])
        q = self._kin.ikine(target)
        self.assertIsNotNone(q)
        back = self._kin.fkine(q)
        self.assertLess(float(np.linalg.norm(back - target)), 0.01)

    def test_ikine_unreachable_returns_none(self):
        # a target far beyond the reach -> no convergence
        q = self._kin.ikine([5.0, 5.0, 5.0])
        self.assertIsNone(q)


if __name__ == "__main__":
    unittest.main()
