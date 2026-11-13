"""E2 library-convergence protocol (docs/03 section 6). C1 main conclusion.

MUST support --dry-run that prints the protocol only and NEVER emits fabricated numbers.
"""
from __future__ import annotations

import argparse

# Comparison set (docs/03 §6 + PROMPT.md ①). SSS original is C2 (requires DAgger training),
# so it is NOT in this training-free comparison.
METHODS = ("pasd_full", "tgl_skill", "ablation_no_gate1", "no_memory")
EPISODES = 200
SEEDS = 3
METRICS = ("|B_t| curve", "FTR", "precision@k")

PROTOCOL = {
    "experiment": "E2",
    "purpose": "C1 main conclusion: bounded (cluster-dedup) vs unbounded (episode-level) experience library",
    "methods": METHODS,
    "episodes_per_method": EPISODES,
    "seeds": SEEDS,
    "metrics": METRICS,
    "metrics_entry": "integration/metrics.py (single source, fairness #11)",
    "expectation": (
        "pasd_full: |B_t| converges to <= k (Gate1 identity dedup); "
        "tgl_skill: |B_t| grows with t (episode-level Skill Blocks, no dedup); "
        "ablation_no_gate1: |B_t| grows linearly in t; no_memory: |B_t| == 0."
    ),
    "status": "protocol + expectation — E2 full run is NOT reproduced; the only reproduced datum "
              "is the FTR range 15%-26% (docs/03 §6, CLAUDE.md §8). Do not pre-fill |B_t| curves.",
}


def main() -> None:
    p = argparse.ArgumentParser(description="E2 library-convergence protocol")
    p.add_argument("--dry-run", action="store_true", help="print protocol only, no numbers")
    args = p.parse_args()
    if args.dry_run:
        for key, value in PROTOCOL.items():
            print(f"{key}: {value}")
        return
    raise NotImplementedError(
        "E2 full run is not yet reproduced: it needs the MuJoCo/real backend (Gate2 simulation) "
        "and the E1 240-failure corpus. Use --dry-run to print the protocol."
    )


if __name__ == "__main__":
    main()
