"""Executor dict-return normalization. Contract: docs/01 section 3/8 + design spec."""
import unittest

from src.pasd_life.executor import Executor
from src.pasd_life.robot_api import MockPiPER, RobotAPI
from src.pasd_life.schema import Observation

SRC = "def run(robot):\n    robot.open_gripper()\n    return {\"steps\": 1, \"state\": {\"ok\": True}}\n"


class TestExecutor(unittest.TestCase):
    def test_normalizes_dict_return(self):
        obs = Executor(RobotAPI(MockPiPER({}))).run(SRC)
        self.assertIsInstance(obs, Observation)
        self.assertEqual(obs.steps, 1)
        self.assertEqual(obs.state["ok"], True)

    def test_dict_missing_fields_defaults(self):
        obs = Executor(RobotAPI(MockPiPER({}))).run("def run(robot):\n    return {}\n")
        self.assertEqual(obs.steps, 0)
        self.assertEqual(obs.state, {})

    def test_none_steps_and_state_default(self):
        obs = Executor(RobotAPI(MockPiPER({}))).run(
            "def run(robot):\n    return {\"steps\": None, \"state\": None}\n")
        self.assertEqual(obs.steps, 0)
        self.assertEqual(obs.state, {})


if __name__ == "__main__":
    unittest.main()
