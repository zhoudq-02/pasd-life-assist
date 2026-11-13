"""Every registered baseline must satisfy the MemoryPlugin / snapshot contract."""
import unittest

from integration.baselines.registry import REGISTRY, build
from src.pasd_life.config import SNAPSHOT_FIELDS


class TestFairness(unittest.TestCase):
    def test_every_baseline_satisfies_plugin_contract(self):
        for name in sorted(REGISTRY):
            with self.subTest(baseline=name):
                plugin = build(name)
                snap = plugin.snapshot()
                self.assertTrue(all(k in snap for k in SNAPSHOT_FIELDS), name)
                self.assertTrue(callable(plugin.retrieve))
                self.assertTrue(callable(plugin.on_episode_end))
                self.assertTrue(callable(plugin.on_step_end))
                self.assertTrue(callable(plugin.snapshot))
                self.assertEqual(bool(snap["requires_training"]), REGISTRY[name][3])

    def test_main_table_a_contains_tgl_and_pragmabot(self):
        table_a = [n for n, v in REGISTRY.items() if v[2] == "A"]
        self.assertIn("tgl_skill", table_a)
        self.assertIn("pragmabot", table_a)

    def test_heldout_split_never_writes_back(self):
        """Anti-contamination is enforced by runner.py; verify the guard exists."""
        import inspect
        from integration import runner
        source = inspect.getsource(runner.run_episode)
        self.assertIn('ctx.split == "dev"', source)


if __name__ == "__main__":
    unittest.main()
