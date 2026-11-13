"""Task definitions. Contract: docs/02 section 1."""
from __future__ import annotations

TASKS = {
    "T1": {"name": "slender grasp", "stage": "execution", "error": "GRASP_SLIP"},
    "T2": {"name": "flat sheet", "stage": "execution", "error": "GRASP_IMPOSSIBLE"},
    "T3": {"name": "obstacle side approach", "stage": "planning", "error": "IK_UNREACHABLE"},
    "T4": {"name": "low-texture object", "stage": "perception", "error": "POSE_LOW_CONFIDENCE"},
    "T5": {"name": "occluded grasp", "stage": "perception", "error": "DETECTION_FAILED"},
    "T6": {"name": "placement", "stage": "verification", "error": "PLACEMENT_OFFSET"},
    "T7": {"name": "OOD", "stage": "mixed", "error": ""},
    "A1": {"name": "assistive feeding", "stage": "interaction/safety/execution", "error": "FOOD_SPILL"},
    "A2": {"name": "object retrieval", "stage": "perception/planning/verification",
           "error": "OCCLUSION_RETRIEVE_FAIL"},
}


def auto_success(task_id: str, state: dict) -> bool:
    """Automatic success judgment (no human annotation). Contract: docs/02 section 1."""
    if "success" in state:
        return bool(state["success"])
    if "subgoal_idx" in state and "subgoals_total" in state:
        return int(state.get("subgoal_idx", 0)) >= int(state.get("subgoals_total", 1))
    return bool(state.get("grasp_ok")) or bool(state.get("placed"))


def auto_reset(task_id: str) -> dict:
    """Scripted reset to the task's initial state (offline scaffold)."""
    return {"task": task_id, "subgoal_idx": 0, "success": False}
