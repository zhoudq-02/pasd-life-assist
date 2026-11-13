"""Contract: failure -> Gate1 -> Gate2 -> retrieve -> repaired success."""
import unittest

from src.pasd_life.demo import run_demo


class TestEndToEnd(unittest.TestCase):
    def test_repair_loop(self):
        out = run_demo(verbose=False)
        self.assertFalse(out["episodes"][0][0], "first episode must fail (top grasp slips)")
        self.assertEqual(out["episodes"][0][1], "GRASP_SLIP")
        self.assertTrue(out["episodes"][1][0], "second episode must succeed after repair injection")
        self.assertGreaterEqual(out["final_library_size"], 1)
        self.assertTrue(any(s in ("VERIFIED", "SAFE") for s in out["states"]))


if __name__ == "__main__":
    unittest.main()
