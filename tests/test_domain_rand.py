"""Offline domain-randomization closed loop (C3, docs/01 §7)."""
import unittest

from src.pasd_life.domain_rand import (
    SIM_PARAM_KEYS,
    failure_distribution,
    map_to_sim_params,
    update_from_real_gap,
)
from src.pasd_life.schema import PiPERError, SceneContext, Trace


def _trace(code):
    return Trace.from_error("T1", PiPERError(code, {"aspect_ratio": 5.3}), SceneContext("T1", "rod", "dev", {}))


class TestFailureDistribution(unittest.TestCase):
    def test_normalized(self):
        q = failure_distribution([_trace("GRASP_SLIP"), _trace("GRASP_SLIP"), _trace("DETECTION_FAILED")])
        self.assertAlmostEqual(sum(q.values()), 1.0)
        self.assertAlmostEqual(q["GRASP_SLIP"], 2 / 3)
        self.assertAlmostEqual(q["DETECTION_FAILED"], 1 / 3)

    def test_empty(self):
        self.assertEqual(failure_distribution([]), {})


class TestMapToSimParams(unittest.TestCase):
    def test_shape_and_default(self):
        p = map_to_sim_params({})
        self.assertEqual(set(p), set(SIM_PARAM_KEYS))

    def test_widens_for_long_tail(self):
        p0 = map_to_sim_params({})
        p1 = map_to_sim_params({"GRASP_SLIP": 0.8})
        for k in SIM_PARAM_KEYS:
            self.assertGreater(p1[k][1], p0[k][1])


class TestUpdateFromRealGap(unittest.TestCase):
    def test_no_gap_returns_unchanged(self):
        p = {k: (0.0, 1.0) for k in SIM_PARAM_KEYS}
        out = update_from_real_gap(p, [], [], srcc=1.0)
        self.assertEqual(out, p)

    def test_gap_widens_ranges(self):
        p = {k: (0.0, 1.0) for k in SIM_PARAM_KEYS}
        out = update_from_real_gap(p, [_trace("GRASP_SLIP")], [_trace("DETECTION_FAILED")], srcc=0.5)
        for k in SIM_PARAM_KEYS:
            self.assertGreater(out[k][1], p[k][1])
            self.assertEqual(out[k][0], p[k][0])


if __name__ == "__main__":
    unittest.main()
