"""A2 object retrieval subgoal chain with ordered state checks. Contract: docs/02 section 4."""
from __future__ import annotations

SUBGOALS = (
    "intent_resolve", "scene_graph_lookup", "reachability_occlusion_filter",
    "path_planning", "grasp", "transport", "place", "state_confirm",
)
# TODO(scaffold): each subgoal carries `completed`; previous must complete before advancing.
