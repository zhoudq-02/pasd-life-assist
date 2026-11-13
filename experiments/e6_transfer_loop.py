"""E6 transfer-loop protocol (docs/03 section 6). C3 main conclusion.

MUST support --dry-run that prints the protocol only and NEVER emits fabricated numbers.
"""
from __future__ import annotations

import argparse

PROTOCOL = {
    "experiment": "E6",
    "purpose": "C3 main conclusion: evaluation-driven OFFLINE simulation-parameter distribution update (q_t(c) -> p_t(theta))",
    "methods": ("adaptive_randomization", "fixed_uniform_sampling"),
    "rounds": 3,
    "metrics": ("SRCC", "sim_real_gap", "long_tail_failure_rate"),
    "metrics_entry": "integration/metrics.py (single source, fairness #11)",
    "offline_only": "q_t(c) -> p_t(theta) only; no online fine-tuning / no inference-pointer switching (CN122735765A)",
    "expectation": (
        "adaptive_randomization: sim/real gap and long-tail failure rate fall across the 3 "
        "rounds (the distribution shifts toward the measured failure types). "
        "fixed_uniform_sampling: distribution unchanged, gap stays constant."
    ),
    "status": "protocol + expectation — E6 full run is NOT reproduced; requires sim + real "
              "trajectories and SRCC. Do not pre-fill numbers.",
}


def main() -> None:
    p = argparse.ArgumentParser(description="E6 transfer-loop protocol")
    p.add_argument("--dry-run", action="store_true", help="print protocol only, no numbers")
    args = p.parse_args()
    if args.dry_run:
        for key, value in PROTOCOL.items():
            print(f"{key}: {value}")
        return
    raise NotImplementedError(
        "E6 full run is not yet reproduced: it needs sim + real trajectories and SRCC. "
        "Use --dry-run to print the protocol."
    )


if __name__ == "__main__":
    main()
