"""Run the end-to-end smoke loop."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pasd_life.demo import run_demo  # noqa: E402

if __name__ == "__main__":
    run_demo()
