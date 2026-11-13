"""Scene-graph observable projection + stats (bootstrap / Wilcoxon / Holm)."""
import unittest

from experiments.stats import holm_correction, paired_bootstrap_ci, wilcoxon_signed_rank
from src.pasd_life.scene_graph import SceneGraph, SceneNode
from src.pasd_life.schema import REAL_OBSERVABLE_FIELDS


class TestSceneGraph(unittest.TestCase):
    def test_observable_features_whitelisted(self):
        g = SceneGraph()
        g.upsert(SceneNode("obj1", (0.3, 0.0, 0.1), affordance="graspable", confidence=0.9))
        feats = g.observable_features()
        self.assertIn("pose_confidence", feats)
        for k in feats:
            self.assertIn(k, REAL_OBSERVABLE_FIELDS)

    def test_feasibility_missing_target(self):
        g = SceneGraph()
        ok, reason = g.feasibility({"target_object": "missing"})
        self.assertFalse(ok)
        self.assertIn("missing", reason)

    def test_feasibility_affordance_mismatch(self):
        g = SceneGraph()
        g.upsert(SceneNode("cup", (0.3, 0.0, 0.1), affordance="graspable", confidence=0.9))
        ok, _ = g.feasibility({"target_object": "cup", "affordance": "pushable"})
        self.assertFalse(ok)


class TestStats(unittest.TestCase):
    def test_bootstrap_ci_identical(self):
        lo, hi = paired_bootstrap_ci([0.8] * 20, [0.8] * 20, seed=0)
        self.assertAlmostEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.0)

    def test_bootstrap_ci_separable(self):
        lo, hi = paired_bootstrap_ci([0.9] * 20, [0.5] * 20, seed=0)
        self.assertGreater(lo, 0.0)

    def test_wilcoxon_identical(self):
        self.assertAlmostEqual(wilcoxon_signed_rank([0.5] * 20, [0.5] * 20), 1.0)

    def test_holm_monotonic_and_bounded(self):
        adjusted = holm_correction([0.01, 0.02, 0.03])
        self.assertEqual(adjusted, sorted(adjusted))
        self.assertGreaterEqual(adjusted[-1], 0.03)
        self.assertLessEqual(adjusted[-1], 1.0)


if __name__ == "__main__":
    unittest.main()
