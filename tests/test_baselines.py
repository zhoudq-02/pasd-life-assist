"""Main-table-A memory baselines: trajectory / episodic / pragmabot (docs/03 §3)."""
import unittest

from integration.baselines.episodic import EpisodicReplay
from integration.baselines.pragmabot import PragmabotMemory
from integration.baselines.trajectory import TrajectoryStorage
from src.pasd_life.schema import Observation, PiPERError, SceneContext, StepFeedback, Trace


def _ctx():
    return SceneContext("T1", "slender rod", "dev", {"aspect_ratio": 5.3})


def _fail(code="GRASP_SLIP"):
    return Trace.from_error("T1", PiPERError(code, {"aspect_ratio": 5.3}), _ctx())


def _success():
    return Trace.from_success("T1", Observation(state={"elapsed": 1.0}, steps=3), _ctx())


class TestTrajectory(unittest.TestCase):
    def test_only_success_stored(self):
        m = TrajectoryStorage()
        m.on_episode_end(_success())
        m.on_episode_end(_fail())
        self.assertEqual(len(m.items), 1)

    def test_retrieve_unverified(self):
        m = TrajectoryStorage()
        m.on_episode_end(_success())
        hints = m.retrieve(_ctx())
        self.assertEqual(len(hints), 1)
        self.assertFalse(hints[0].verified)
        self.assertEqual(hints[0].verified_by, "none")


class TestEpisodic(unittest.TestCase):
    def test_both_outcomes_stored(self):
        m = EpisodicReplay()
        m.on_episode_end(_success())
        m.on_episode_end(_fail())
        self.assertEqual(len(m.items), 2)

    def test_retrieve_replays(self):
        m = EpisodicReplay()
        m.on_episode_end(_fail())
        hints = m.retrieve(_ctx())
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].verified_by, "none")


class TestPragmabot(unittest.TestCase):
    def test_step_reflection_into_stm(self):
        m = PragmabotMemory()
        m.on_step_end(StepFeedback({}, {}, {}, 0))
        self.assertEqual(len(m.stm), 1)
        self.assertEqual(m.fm_calls, 1)

    def test_success_writes_ltm_and_clears_stm(self):
        m = PragmabotMemory()
        m.on_step_end(StepFeedback({}, {}, {}, 0))
        m.on_episode_end(_success())
        self.assertEqual(len(m.ltm), 1)
        self.assertEqual(len(m.stm), 0)

    def test_failure_does_not_write_ltm(self):
        m = PragmabotMemory()
        m.on_step_end(StepFeedback({}, {}, {}, 0))
        m.on_episode_end(_fail())
        self.assertEqual(len(m.ltm), 0)
        self.assertEqual(len(m.stm), 0)

    def test_retrieve_returns_ltm_hint(self):
        m = PragmabotMemory()
        m.on_episode_end(_success())
        hints = m.retrieve(_ctx())
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].verified_by, "none")


if __name__ == "__main__":
    unittest.main()
