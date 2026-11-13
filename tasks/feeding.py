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
# TODO(scaffold): ordered subgoal validation (no cascade), auto success + auto reset.
