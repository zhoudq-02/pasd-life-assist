"""Single metrics entry point: SR / S3R / Delta."""
import unittest

from integration import metrics


class TestMetrics(unittest.TestCase):
    def test_sr_s3r_and_delta_expose_hidden_instability(self):
        records = [
            {"success": True, "s3r": False},
            {"success": True, "s3r": True},
            {"success": False, "s3r": False},
        ]
        self.assertEqual(metrics.sr(records), 2 / 3)
        self.assertEqual(metrics.s3r(records), 1 / 3)
        self.assertAlmostEqual(metrics.delta(records), 1 / 3)

    def test_empty_records_do_not_crash(self):
        self.assertEqual(metrics.sr([]), 0.0)
        self.assertEqual(metrics.s3r([]), 0.0)

    def test_false_promotion_rate_is_none_aware(self):
        self.assertEqual(metrics.false_promotion_rate([]), 0.0)


if __name__ == "__main__":
    unittest.main()
