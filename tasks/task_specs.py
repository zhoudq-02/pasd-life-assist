"""Task definitions. Contract: docs/02 section 1. TODO(scaffold): auto success + auto reset."""
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
