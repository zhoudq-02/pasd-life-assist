"""E5 generalization protocol (docs/03 section 6). RQ4.

MUST support --dry-run that prints the protocol only and NEVER emits fabricated numbers.
"""
from __future__ import annotations

import argparse

PROTOCOL = {
    "experiment": "E5",
    "purpose": "RQ4: generalization to unseen objects + cross-task signature reuse",
    "methods": ("pasd_full", "tgl_skill"),
    "splits": ("seen", "unseen"),
    "metrics": ("zero_shot_SR", "cluster_reuse_rate"),
    "metrics_entry": "integration/metrics.py (single source, fairness #11)",
    "status": "protocol + expectation — E5 full run is NOT reproduced; requires sim/real backend",
}


def main() -> None:
    p = argparse.ArgumentParser(description="E5 generalization protocol")
    p.add_argument("--dry-run", action="store_true", help="print protocol only, no numbers")
    args = p.parse_args()
    if args.dry_run:
        for key, value in PROTOCOL.items():
            print(f"{key}: {value}")
        return
    raise NotImplementedError(
        "E5 full run is not yet reproduced: needs the sim/real backend. Use --dry-run."
    )


if __name__ == "__main__":
    main()
