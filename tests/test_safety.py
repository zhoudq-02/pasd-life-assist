"""Safety envelope -> specific error code mapping (C2, docs/02 §3)."""
import unittest

from src.pasd_life.safety import SAFETY_CODE_BY_FIELD, SafetyEnvelope


class TestSafetyEnvelope(unittest.TestCase):
    def test_classify_mouth_approach_unsafe(self):
        self.assertEqual(SafetyEnvelope().classify({"min_human_dist": 0.05}), "MOUTH_APPROACH_UNSAFE")
        self.assertEqual(SafetyEnvelope().classify({"eef_speed": 0.9}), "MOUTH_APPROACH_UNSAFE")

    def test_classify_food_spill(self):
        self.assertEqual(SafetyEnvelope().classify({"tilt_angle": 45.0}), "FOOD_SPILL")
        self.assertEqual(SafetyEnvelope().classify({"fill_level": 0.9}), "FOOD_SPILL")

    def test_classify_safety_violation(self):
        self.assertEqual(SafetyEnvelope().classify({"contact_force": 20.0}), "SAFETY_VIOLATION")
        self.assertEqual(SafetyEnvelope().classify({"food_temp": 60.0}), "SAFETY_VIOLATION")

    def test_classify_none_when_safe(self):
        self.assertIsNone(SafetyEnvelope().classify({"min_human_dist": 0.4, "eef_speed": 0.1}))

    def test_violated_reason_names_code(self):
        violated, reason = SafetyEnvelope().violated({"min_human_dist": 0.05})
        self.assertTrue(violated)
        self.assertIn("MOUTH_APPROACH_UNSAFE", reason)

    def test_all_six_fields_mapped(self):
        self.assertEqual(
            set(SAFETY_CODE_BY_FIELD),
            {"min_human_dist", "eef_speed", "tilt_angle", "fill_level", "contact_force", "food_temp"},
        )


if __name__ == "__main__":
    unittest.main()
