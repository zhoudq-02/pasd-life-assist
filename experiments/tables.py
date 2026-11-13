"""Result tables A / B / C1 / C2 / D. Contract: docs/03 section 2/5.

Main conclusions come ONLY from A/B; C1/C2 report trends with budget annotation and are
never significance-tested against A. false_promotion_rate is N/A (None) for methods without
a promotion state machine.
"""
from __future__ import annotations

COLUMNS_A = ("method", "SR", "S3R", "ET", "CR", "Delta", "library_size", "false_promotion_rate")
COLUMNS_C = ("method", "budget", "trend")


def markdown_table(headers, rows) -> str:
    """Render headers + rows as a GitHub-flavoured markdown table."""
    lines = ["| " + " | ".join(str(h) for h in headers) + " |",
             "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def main_table_a(rows: list[dict]) -> str:
    """Main table A: conclusions come ONLY from A/B (docs/03 §5)."""
    return markdown_table(COLUMNS_A, [[r.get(c, "") for c in COLUMNS_A] for r in rows])


def c_table(rows: list[dict]) -> str:
    """C1/C2 trend table with budget annotation; never significance-tested vs A."""
    return markdown_table(COLUMNS_C, [[r.get(c, "") for c in COLUMNS_C] for r in rows])


def false_promotion_rate_cell(value) -> str:
    """Render N/A for methods without a promotion state machine (never '0')."""
    return "N/A" if value is None else str(value)
