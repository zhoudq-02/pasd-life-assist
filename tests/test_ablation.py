"""Main-table-B ablation switches (docs/03 §2)."""
import unittest

from integration.baselines.ablation import build_ablation
from src.pasd_life.schema import PiPERError, SceneContext, Trace


def _ctx():
    return SceneContext("T1", "rod", "dev", {"aspect_ratio": 5.3})


def _fail():
    return Trace.from_error("T1", PiPERError("GRASP_SLIP", {"aspect_ratio": 5.3}), _ctx())


class _FailSimRunner:
    def run(self, skill) -> bool:
        return False


class TestAblation(unittest.TestCase):
    def test_no_gate1_no_dedup(self):
        m = build_ablation("no_gate1")
        m.on_episode_end(_fail())
        m.on_episode_end(_fail())
        self.assertEqual(m.library.size, 2)

    def test_no_gate2_verified_despite_failing_sim(self):
        m = build_ablation("no_gate2", sim_runner=_FailSimRunner())
        m.on_episode_end(_fail())
        self.assertEqual(m.library.verified_count, 1)

    def test_no_gate3_reaches_safe(self):
        m = build_ablation("no_gate3")
        m.on_episode_end(_fail())
        self.assertIn("SAFE", [s.state for s in m.library.all()])

    def test_unknown_ablation_raises(self):
        with self.assertRaises(KeyError):
            build_ablation("bogus")


if __name__ == "__main__":
    unittest.main()
