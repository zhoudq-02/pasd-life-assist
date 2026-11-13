"""Paired bootstrap 95% CI / Wilcoxon signed-rank / Holm correction."""
from __future__ import annotations

import math
import random


def paired_bootstrap_ci(a, b, n: int = 2000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float]:
    """95% CI for the paired difference mean(a - b), via bootstrap resampling."""
    if len(a) != len(b) or not a:
        return (0.0, 0.0)
    rng = random.Random(seed)
    diffs = [x - y for x, y in zip(a, b)]
    means = []
    for _ in range(n):
        sample = [diffs[rng.randrange(len(diffs))] for _ in range(len(diffs))]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo = means[int((alpha / 2.0) * n)]
    hi = means[int((1.0 - alpha / 2.0) * n) - 1]
    return (lo, hi)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def wilcoxon_signed_rank(a, b) -> float:
    """Two-sided Wilcoxon signed-rank p-value (normal approximation with tie ranks)."""
    if len(a) != len(b):
        raise ValueError("paired samples must have equal length")
    non_zero = [x - y for x, y in zip(a, b) if x != y]
    n = len(non_zero)
    if n == 0:
        return 1.0
    abs_diffs = sorted((abs(d), i) for i, d in enumerate(non_zero))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and abs_diffs[j][0] == abs_diffs[i][0]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[abs_diffs[k][1]] = avg
        i = j
    W = sum(ranks[i] for i, d in enumerate(non_zero) if d > 0)
    mean_W = n * (n + 1) / 4.0
    var_W = n * (n + 1) * (2 * n + 1) / 24.0
    z = (W - mean_W) / math.sqrt(var_W)
    p = 2.0 * (1.0 - _norm_cdf(abs(z)))
    return max(0.0, min(1.0, p))


def holm_correction(p_values) -> list[float]:
    """Holm-Bonferroni adjusted p-values (monotonic, bounded to [0, 1])."""
    m = len(p_values)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    prev = 0.0
    for rank, idx in enumerate(order):
        adj = min(1.0, p_values[idx] * (m - rank))
        adjusted[idx] = max(prev, adj)
        prev = adjusted[idx]
    return adjusted
