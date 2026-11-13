"""E3 dual-task end-to-end protocol (docs/03 section 6). C1+C2+C3.

MUST support --dry-run that prints the protocol only and NEVER emits fabricated numbers.
"""
from __future__ import annotations

import argparse

PROTOCOL = {
    "experiment": "E3",
    "purpose": "C1+C2+C3: dual-task end-to-end on main table A (training-free baselines)",
    "methods": ("no_memory", "trajectory_storage", "episodic_replay", "pasd",
                "pragmabot", "tgl_skill", "pasd_full"),
    "tasks": ("A1", "A2"),
    "instructions": "7 simple / 4 implicit / 13 composed per task, 50 rounds each, 30-step cap (docs/02 §2)",
    "metrics": ("SR", "S3R", "ET", "CR", "Delta"),
    "metrics_entry": "integration/metrics.py (single source, fairness #11)",
    "status": "protocol + expectation — E3 full run is NOT reproduced; requires sim/real backend",
}


def main() -> None:
    p = argparse.ArgumentParser(description="E3 dual-task end-to-end protocol")
    p.add_argument("--dry-run", action="store_true", help="print protocol only, no numbers")
    args = p.parse_args()
    if args.dry_run:
        for key, value in PROTOCOL.items():
            print(f"{key}: {value}")
        return
    raise NotImplementedError(
        "E3 full run is not yet reproduced: needs the sim/real backend. Use --dry-run."
    )


if __name__ == "__main__":
    main()
