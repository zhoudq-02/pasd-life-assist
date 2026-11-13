"""OFFLINE simulation-parameter distribution update (C3). Contract: docs/01 section 7.

HARD BOUNDARY: no online fine-tuning, no incremental training-data generation,
no inference-pointer switching, no atomic deployment switch (CN122735765A).
"""
from __future__ import annotations

SIM_PARAM_KEYS = ("friction", "mass", "light_texture", "sensor_noise", "action_latency")


def failure_distribution(traces) -> dict[str, float]:
    """q_t(c): distribution over failure-signature clusters from evaluation logs."""
    counts: dict[str, int] = {}
    for t in traces:
        code = getattr(t, "error_code", "") or "none"
        counts[code] = counts.get(code, 0) + 1
    total = sum(counts.values()) or 1
    return {k: v / total for k, v in counts.items()}


def map_to_sim_params(q: dict[str, float], current: dict | None = None) -> dict:
    """p_t(theta): map long-tail failure clusters to randomised simulator parameters."""
    base = {k: (0.0, 1.0) for k in SIM_PARAM_KEYS}
    if current:
        base.update(current)
    worst = max(q.values()) if q else 0.0
    for key in SIM_PARAM_KEYS:
        lo, hi = base[key]
        base[key] = (lo, hi + worst)  # widen the range for long-tail clusters
    return base


def update_from_real_gap(p: dict, sim_traces, real_traces, srcc: float) -> dict:
    """Offline closed loop: adjust p by the sim/real trajectory discrepancy."""
    # TODO(scaffold): real SRCC computation with paired trajectories, per-cluster
    # reweighting of slip/occlusion/collision/recovery states, convergence test.
    if srcc < 0.0:
        return {k: (lo, hi * 1.1) for k, (lo, hi) in p.items()}
    return dict(p)
