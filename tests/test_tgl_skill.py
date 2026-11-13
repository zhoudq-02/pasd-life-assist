"""TGL proxy: Skill Block + Experience Memory + five admission checks (docs/03 §3)."""
import unittest

from integration.baselines.tgl_skill import TGLSkillMemory
from src.pasd_life.schema import Observation, PiPERError, SceneContext, Trace


def _ctx():
    return SceneContext("T1", "slender rod", "dev", {"aspect_ratio": 5.3})


def _fail_trace(code="GRASP_SLIP", features=None):
    return Trace.from_error("T1", PiPERError(code, features or {"aspect_ratio": 5.3}), _ctx())


class TestTGLSkill(unittest.TestCase):
    def test_starts_empty(self):
        mem = TGLSkillMemory()
        self.assertEqual(mem.retrieve(_ctx()), [])
        self.assertEqual(mem.snapshot()["library_size"], 0)

    def test_repairable_failure_admits_block(self):
        mem = TGLSkillMemory()
        mem.on_episode_end(_fail_trace())
        self.assertEqual(len(mem.experience), 1)
        self.assertEqual(len(mem.skill_blocks), 1)
        self.assertEqual(mem.snapshot()["library_size"], 1)
        self.assertEqual(mem.snapshot()["verified"], 1)

    def test_retrieve_returns_admission_checked_hint(self):
        mem = TGLSkillMemory()
        mem.on_episode_end(_fail_trace())
        hints = mem.retrieve(_ctx())
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].verified_by, "admission_check")
        self.assertTrue(hints[0].verified)
        self.assertEqual(hints[0].executable["fixes"], "GRASP_SLIP")

    def test_non_repairable_not_admitted(self):
        mem = TGLSkillMemory()
        mem.on_episode_end(_fail_trace("IK_UNREACHABLE", {}))
        self.assertEqual(len(mem.experience), 1)
        self.assertEqual(len(mem.skill_blocks), 0)

    def test_duplicate_failure_dedups(self):
        mem = TGLSkillMemory()
        mem.on_episode_end(_fail_trace())
        mem.on_episode_end(_fail_trace())
        self.assertEqual(len(mem.skill_blocks), 1)

    def test_success_recorded_but_no_block(self):
        mem = TGLSkillMemory()
        mem.on_episode_end(Trace.from_success("T1", Observation(state={"elapsed": 1.0}, steps=3), _ctx()))
        self.assertEqual(len(mem.experience), 1)
        self.assertEqual(len(mem.skill_blocks), 0)


if __name__ == "__main__":
    unittest.main()
