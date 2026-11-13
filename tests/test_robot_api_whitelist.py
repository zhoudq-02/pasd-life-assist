"""Whitelist, anti-contamination and PiPER physical-semantics contract tests."""
import unittest

from src.pasd_life.executor import Executor
from src.pasd_life.robot_api import ALLOWED, MockPiPER, RobotAPI, WhitelistViolation
from src.pasd_life.schema import PiPERError


class TestRobotAPI(unittest.TestCase):
    def test_whitelist_blocks_unknown_primitive(self):
        api = RobotAPI(MockPiPER({}))
        with self.assertRaises(WhitelistViolation):
            api.call("read_simulation_truth")
        self.assertEqual(len(ALLOWED), 5)

    def test_observation_has_no_simulation_ground_truth(self):
        api = RobotAPI(MockPiPER({"ground_truth_mass": 0.12, "pose_confidence": 0.9}))
        obs = api.get_observation()
        self.assertNotIn("ground_truth_mass", obs)
        self.assertEqual(obs["pose_confidence"], 0.9)

    def test_policy_ast_rejects_imports_and_non_whitelisted_calls(self):
        api = RobotAPI(MockPiPER({}))
        with self.assertRaises(WhitelistViolation):
            Executor(api)._compile("import os\n\ndef run(robot):\n    robot.open_gripper()\n")
        with self.assertRaises(WhitelistViolation):
            Executor(api)._compile("def run(robot):\n    robot.backend.step('x')\n")

    def test_slender_top_grasp_raises_grasp_slip(self):
        api = RobotAPI(MockPiPER({"aspect_ratio": 5.3, "approach": "top", "target_width": 0.022}))
        with self.assertRaises(PiPERError) as ctx:
            api.move_to_pose({"approach": "top"})
            api.close_gripper(width=0.022)
        self.assertEqual(ctx.exception.error_code, "GRASP_SLIP")


if __name__ == "__main__":
    unittest.main()
