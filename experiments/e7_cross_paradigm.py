"""E7 cross-paradigm positioning protocol (docs/03 section 6).

MUST support --dry-run that prints the protocol only and NEVER emits fabricated numbers.
"""
from __future__ import annotations

import argparse

PROTOCOL = {
    "experiment": "E7",
    "purpose": "positioning: cross-paradigm comparison with budget annotation",
    "methods": ("sss", "soar", "armada", "neerl", "rlingua", "vla_proxy"),
    "budget_annotation": "training / demo / human budget per method (docs/03 §3); "
                         "NO significance test against main table A",
    "metrics": "trends only (C2 is reported separately from main table A/B)",
    "status": "protocol + expectation — E7 full run is NOT reproduced; requires training budgets",
}


def main() -> None:
    p = argparse.ArgumentParser(description="E7 cross-paradigm positioning protocol")
    p.add_argument("--dry-run", action="store_true", help="print protocol only, no numbers")
    args = p.parse_args()
    if args.dry_run:
        for key, value in PROTOCOL.items():
            print(f"{key}: {value}")
        return
    raise NotImplementedError(
        "E7 full run is not yet reproduced: needs training budgets. Use --dry-run."
    )


if __name__ == "__main__":
    main()
