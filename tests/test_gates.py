"""Three-gate lifecycle and safety-veto contract tests."""
import unittest

from src.pasd_life.executor import MockSimRunner
from src.pasd_life.gates import gate1_observe_failure, gate3_verify, promote, propose_repair
from src.pasd_life.pasd_core import Extractor, OnlineClusterer, SkillLibrary
from src.pasd_life.safety import SafetyEnvelope
from src.pasd_life.schema import PiPERError, SceneContext, Trace


def _trace(code="GRASP_SLIP", features=None):
    ctx = SceneContext("T1", "slender rod", "dev", {"aspect_ratio": 5.3})
    return Trace.from_error("T1", PiPERError(code, features or {"aspect_ratio": 5.3}), ctx)


class TestGates(unittest.TestCase):
    def test_gate1_deduplicates_by_cluster_identity(self):
        ex, cl, lib = Extractor(), OnlineClusterer(), SkillLibrary()
        first = gate1_observe_failure(_trace(), ex, cl, lib)
        self.assertIsNotNone(first)
        self.assertEqual(first.state, "CANDIDATE")
        self.assertIsNone(gate1_observe_failure(_trace(), ex, cl, lib))
        self.assertEqual(lib.size, 1)

    def test_non_repairable_mode_returns_none(self):
        self.assertIsNone(propose_repair(_trace("IK_UNREACHABLE", {})))
        self.assertIsNone(propose_repair(_trace("INTENT_AMBIGUOUS", {"intent_confidence": 0.4})))

    def test_safety_envelope_vetoes_even_when_gate2_would_pass(self):
        ex, cl, lib = Extractor(), OnlineClusterer(), SkillLibrary()
        skill = gate1_observe_failure(_trace(), ex, cl, lib)
        result = promote(skill, sim_runner=MockSimRunner({"aspect_ratio": 5.3}),
                         features={"min_human_dist": 0.05}, envelope=SafetyEnvelope())
        self.assertEqual(result.state, "REJECTED")
        self.assertIn("safety_envelope", result.verification["veto"])

    def test_gate3_requires_eight_successes_and_human_confirmation(self):
        ex, cl, lib = Extractor(), OnlineClusterer(), SkillLibrary()
        skill = gate1_observe_failure(_trace(), ex, cl, lib)
        promote(skill, sim_runner=MockSimRunner({"aspect_ratio": 5.3}))
        self.assertEqual(skill.state, "VERIFIED")
        self.assertFalse(gate3_verify(skill, {"consecutive_success": 7}, human_confirmed=True))
        self.assertFalse(gate3_verify(skill, {"consecutive_success": 8}, human_confirmed=False))
        self.assertTrue(gate3_verify(skill, {"consecutive_success": 8}, human_confirmed=True,
                                     envelope=SafetyEnvelope(), features={"min_human_dist": 0.4}))


if __name__ == "__main__":
    unittest.main()
