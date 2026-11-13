"""_load_dotenv inline-comment stripping. Contract: docs/08 section 5 / design spec."""
import os
import tempfile
import unittest
from pathlib import Path

from src.pasd_life.settings import _load_dotenv


class TestDotenv(unittest.TestCase):
    def _load(self, text):
        d = tempfile.mkdtemp()
        p = Path(d) / ".env"
        p.write_text(text, encoding="utf-8")
        _load_dotenv(p)
        for k in ("PASD_T_BACKEND", "PASD_T_REAL", "PASD_T_QUOTED", "PASD_T_EXP", "PASD_T_URL"):
            self.addCleanup(os.environ.pop, k, None)

    def test_strips_inline_comment(self):
        self._load("PASD_T_BACKEND=mock            # mock | mujoco | real\n")
        self.assertEqual(os.environ.get("PASD_T_BACKEND"), "mock")

    def test_keeps_export_and_quotes(self):
        self._load("export PASD_T_EXP=mock\nPASD_T_QUOTED=\"dev\"\n")
        self.assertEqual(os.environ.get("PASD_T_EXP"), "mock")
        self.assertEqual(os.environ.get("PASD_T_QUOTED"), "dev")

    def test_hash_inside_quotes_preserved(self):
        self._load('PASD_T_URL="http://x/#frag"\n')
        self.assertEqual(os.environ.get("PASD_T_URL"), "http://x/#frag")


if __name__ == "__main__":
    unittest.main()
