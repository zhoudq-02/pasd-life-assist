"""The ONLY metrics implementation (fairness checklist #11). No baseline may bypass it."""
from __future__ import annotations


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sr(records: list[dict]) -> float:
    return _mean([1.0 if r.get("success") else 0.0 for r in records])


def s3r(records: list[dict]) -> float:
    """S3R: success AND stable AND safe (docs/01 section 6)."""
    return _mean([1.0 if r.get("s3r") else 0.0 for r in records])


def delta(records: list[dict]) -> float:
    return sr(records) - s3r(records)


def et(records: list[dict]) -> float:
    return _mean([float(r.get("elapsed", 0.0)) for r in records])


def cr(records: list[dict]) -> float:
    return _mean([float(r.get("subgoal_ratio", 0.0)) for r in records])


def ftr(traces, verified_count: int) -> float:
    """Failure-to-repair rate: VERIFIED repairs / total failures."""
    failures = [t for t in traces if getattr(t, "error_code", "")]
    return verified_count / len(failures) if failures else 0.0


def cluster_purity(assignments: list[int], ground_truth: list[int]) -> float:
    if not assignments:
        return 0.0
    groups: dict[int, list[int]] = {}
    for a, g in zip(assignments, ground_truth):
        groups.setdefault(a, []).append(g)
    majority = sum(v.count(max(set(v), key=v.count)) for v in groups.values())
    return majority / len(assignments)


def false_promotion_rate(skills) -> float | None:
    """Only defined for methods WITH a promotion state machine; else return None (N/A)."""
    promoted = [s for s in skills if getattr(s, "state", "") in ("VERIFIED", "SAFE")]
    if not promoted:
        return 0.0
    bad = sum(1 for s in promoted if float(s.verification.get("gate2_rate", 0.0)) < 0.80)
    return bad / len(promoted)
