"""E4 safety-ablation protocol (docs/03 section 6). C2 main conclusion.

MUST support --dry-run that prints the protocol only and NEVER emits fabricated numbers.
"""
from __future__ import annotations

import argparse

PROTOCOL = {
    "experiment": "E4",
    "purpose": "C2 main conclusion: safety envelope + Gate3 as a necessary promotion condition",
    "methods": ("full_system", "ablation_no_gate3"),
    "human_proxy": "fake head model first (real users only after the E4 Gate3 ablation)",
    "metrics": ("min_human_dist", "dangerous_approach_count", "estop_count", "mis_feed_count"),
    "metrics_entry": "integration/metrics.py (single source, fairness #11)",
    "expectation": (
        "full_system: larger min_human_dist, fewer dangerous approaches / estops / mis-feeds; "
        "a repair that passes Gate2 but violates the safety envelope is REJECTED, and "
        "INTENT_AMBIGUOUS routes to human instead of auto-promoting. "
        "ablation_no_gate3: the Gate3 safety gate is removed, so unsafe repairs may reach deployment."
    ),
    "status": "protocol + expectation — E4 full run is NOT reproduced; requires the fake-head "
              "setup + real/sim backend. Do not pre-fill safety numbers.",
}


def main() -> None:
    p = argparse.ArgumentParser(description="E4 safety-ablation protocol")
    p.add_argument("--dry-run", action="store_true", help="print protocol only, no numbers")
    args = p.parse_args()
    if args.dry_run:
        for key, value in PROTOCOL.items():
            print(f"{key}: {value}")
        return
    raise NotImplementedError(
        "E4 full run is not yet reproduced: it needs the fake-head model + real/sim backend. "
        "Use --dry-run to print the protocol."
    )


if __name__ == "__main__":
    main()
