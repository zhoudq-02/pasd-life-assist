"""The single automatic success criterion (fairness checklist #4)."""
from __future__ import annotations


def judge(task: str, state: dict) -> bool:
    if "success" in state:
        return bool(state["success"])
    total = float(state.get("subgoals_total", 1.0) or 1.0)
    done = float(state.get("subgoals_completed", 0.0))
    return bool(state.get("grasp_ok")) or done >= total
