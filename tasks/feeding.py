"""A1 assistive feeding subgoal chain. Contract: docs/02 section 3."""
from __future__ import annotations

SUBGOALS = (
    "intent_parse", "target_locate", "pose_fill_temp_check", "reachability_safety_precheck",
    "utensil_grasp", "scoop_or_pour", "deliver_to_mouth_safe_zone", "state_confirm", "retract_reset",
)
STATE_FIELDS = (
    "utensil_pose", "fill_level", "food_temp", "human_mouth_pose", "min_human_dist",
    "gripper_width", "pose_confidence", "subgoal_idx", "intent_confidence",
    "tilt_angle", "eef_speed", "contact_force",
)
def subgoal_advance_ok(state: dict, next_idx: int) -> bool:
    """Ordered subgoal validation: subgoal_idx advances one step at a time (no cascade)."""
    cur = int(state.get("subgoal_idx", 0))
    return next_idx == cur + 1 and 0 <= next_idx <= len(SUBGOALS)


def auto_success(state: dict) -> bool:
    """A1 complete: terminal subgoal reached (no human annotation)."""
    if "success" in state:
        return bool(state["success"])
    return int(state.get("subgoal_idx", 0)) >= len(SUBGOALS)


def auto_reset() -> dict:
    """Initial A1 state: subgoal_idx=0 and safe defaults for the safety-relevant fields."""
    return {
        "subgoal_idx": 0, "success": False, "intent_confidence": 0.0,
        "pose_confidence": 0.0, "min_human_dist": 0.5, "eef_speed": 0.0,
        "contact_force": 0.0, "tilt_angle": 0.0, "fill_level": 0.0,
        "food_temp": 20.0, "gripper_width": 0.0,
    }
