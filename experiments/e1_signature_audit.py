"""E1 signature-audit protocol (docs/03 section 6). C1 precondition.

MUST support --dry-run that prints the protocol only and NEVER emits fabricated numbers.
"""
from __future__ import annotations

import argparse

PROTOCOL = {
    "experiment": "E1",
    "purpose": "C1 precondition: signature extraction + online clustering quality",
    "threshold_strategies": ("observed", "margin", "quantized", "split"),
    "corpus": "240 failures",
    "metrics": ("cluster_count", "purity", "dedup_rate"),
    "reproduced": "240 -> 9 clusters, purity 1.0, dedup 96% (upstream PASD reference; "
                  "the only reproduced E1 datum)",
    "status": "reproduced datum from upstream; a full re-run needs the 240-failure corpus",
}


def main() -> None:
    p = argparse.ArgumentParser(description="E1 signature-audit protocol")
    p.add_argument("--dry-run", action="store_true", help="print protocol only, no numbers")
    args = p.parse_args()
    if args.dry_run:
        for key, value in PROTOCOL.items():
            print(f"{key}: {value}")
        return
    raise NotImplementedError(
        "E1 full re-run needs the 240-failure corpus (not shipped). Use --dry-run for the protocol."
    )


if __name__ == "__main__":
    main()
