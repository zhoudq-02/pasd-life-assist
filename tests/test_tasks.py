"""Task-layer auto success / auto reset / ordered subgoal validation (docs/02)."""
import unittest

from tasks.feeding import (
    SUBGOALS as A1_SUBGOALS,
    auto_reset as a1_reset,
    auto_success as a1_success,
    subgoal_advance_ok,
)
from tasks.retrieval import (
    SUBGOALS as A2_SUBGOALS,
    auto_reset as a2_reset,
    auto_success as a2_success,
    subgoal_order_ok,
)
from tasks.task_specs import auto_reset as generic_reset, auto_success as generic_success


class TestFeeding(unittest.TestCase):
    def test_advance_one_step_ok(self):
        self.assertTrue(subgoal_advance_ok({"subgoal_idx": 0}, 1))
        self.assertFalse(subgoal_advance_ok({"subgoal_idx": 0}, 2))   # skip
        self.assertFalse(subgoal_advance_ok({"subgoal_idx": 0}, -1))  # backward
        self.assertFalse(subgoal_advance_ok({"subgoal_idx": 0}, len(A1_SUBGOALS) + 1))  # out of bounds

    def test_success_at_terminal(self):
        self.assertFalse(a1_success({"subgoal_idx": len(A1_SUBGOALS) - 1}))
        self.assertTrue(a1_success({"subgoal_idx": len(A1_SUBGOALS)}))

    def test_reset_initial(self):
        self.assertEqual(a1_reset()["subgoal_idx"], 0)


class TestRetrieval(unittest.TestCase):
    def test_order_contiguous_prefix_ok(self):
        self.assertTrue(subgoal_order_ok([True, True, False, False]))
        self.assertTrue(subgoal_order_ok([True] * 4))
        self.assertTrue(subgoal_order_ok([False] * 4))

    def test_order_gap_rejected(self):
        self.assertFalse(subgoal_order_ok([True, False, True, False]))

    def test_success_all_completed(self):
        self.assertTrue(a2_success([True] * len(A2_SUBGOALS)))
        self.assertFalse(a2_success([True] * (len(A2_SUBGOALS) - 1) + [False]))

    def test_reset_all_false(self):
        self.assertEqual(a2_reset(), [False] * len(A2_SUBGOALS))


class TestTaskSpecs(unittest.TestCase):
    def test_generic_success_flag(self):
        self.assertTrue(generic_success("T1", {"success": True}))
        self.assertFalse(generic_success("T1", {"success": False}))

    def test_generic_reset(self):
        s = generic_reset("T1")
        self.assertEqual(s["task"], "T1")
        self.assertEqual(s["subgoal_idx"], 0)


if __name__ == "__main__":
    unittest.main()
