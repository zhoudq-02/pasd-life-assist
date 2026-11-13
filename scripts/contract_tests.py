"""Zero-dependency contract test runner (stdlib unittest).

The same test files are also discoverable by pytest if it is installed:
    python3 -m pytest -q          # optional
    python3 scripts/contract_tests.py  # always works, no network needed
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"), pattern="test_*.py", top_level_dir=str(ROOT)
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"\nRESULT: {result.testsRun} tests, "
          f"{len(result.failures)} failures, {len(result.errors)} errors")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
