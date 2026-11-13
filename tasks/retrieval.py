"""A2 object retrieval subgoal chain with ordered state checks. Contract: docs/02 section 4."""
from __future__ import annotations

SUBGOALS = (
    "intent_resolve", "scene_graph_lookup", "reachability_occlusion_filter",
    "path_planning", "grasp", "transport", "place", "state_confirm",
)
def subgoal_order_ok(completed) -> bool:
    """Ordered state check: completed flags must form a contiguous prefix (no cascade)."""
    seen_gap = False
    for c in completed:
        if c and seen_gap:
            return False
        if not c:
            seen_gap = True
    return True


def auto_success(completed) -> bool:
    """A2 complete: all subgoals completed."""
    return len(completed) == len(SUBGOALS) and all(completed)


def auto_reset() -> list:
    """Initial A2 completion flags: all False."""
    return [False] * len(SUBGOALS)
