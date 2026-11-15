"""Instruction set protocol: simple 7 / implicit 4 / composed 13 (docs/02 §2)."""
import unittest

from tasks.instructions import INSTRUCTIONS


class TestInstructions(unittest.TestCase):
    def test_counts_7_4_13(self):
        for task in ("A1", "A2"):
            self.assertEqual(len(INSTRUCTIONS[task]["simple"]), 7, task)
            self.assertEqual(len(INSTRUCTIONS[task]["implicit"]), 4, task)
            self.assertEqual(len(INSTRUCTIONS[task]["composed"]), 13, task)

    def test_all_non_empty(self):
        for task in INSTRUCTIONS:
            for cls in INSTRUCTIONS[task]:
                for instr in INSTRUCTIONS[task][cls].values():
                    self.assertTrue(str(instr).strip(), instr)

    def test_given_examples_present(self):
        self.assertIn("把水杯递到嘴边", INSTRUCTIONS["A1"]["simple"].values())
        self.assertIn("帮我喝点汤", INSTRUCTIONS["A1"]["implicit"].values())
        self.assertIn("先舀一勺再递过来", INSTRUCTIONS["A1"]["composed"].values())
        self.assertIn("把水杯拿给我", INSTRUCTIONS["A2"]["simple"].values())
        self.assertIn("我有点渴", INSTRUCTIONS["A2"]["implicit"].values())
        self.assertIn("把药盒和温水一起放到我右手边", INSTRUCTIONS["A2"]["composed"].values())


if __name__ == "__main__":
    unittest.main()
