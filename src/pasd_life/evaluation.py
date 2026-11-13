"""Unified evaluation protocol (C3). Contract: docs/01 section 6."""
from __future__ import annotations

LOG_SCHEMA = {
    "episode_id": "str", "method": "str", "task": "str", "instruction_type": "str",
    "seed": "int", "split": "str", "success": "bool", "s3r": "bool",
    "elapsed": "float", "subgoal_ratio": "float",
    "subgoal_checks": "list", "failure_type": "str", "failure_stage": "str",
    "recovery_attempts": "int", "local_replan_success": "int",
    "min_human_dist": "float", "max_contact_force": "float", "spill": "bool",
    "emergency_stops": "int", "library_size": "int", "verified_by": "str",
    "frame_id": "int", "timestamp": "float",
}


def is_s3r_success(*, success: bool, envelope_ok: bool = True,
                   no_unrecovered_failure: bool = True,
                   no_dangerous_approach: bool = True) -> bool:
    """S3R counts an episode only if it is BOTH completed and stable/safe."""
    return bool(success and envelope_ok and no_unrecovered_failure and no_dangerous_approach)


def capability_profile(records: list[dict]) -> dict:
    """Runtime capability profile; the input of q_t(c) in domain_rand.py."""
    n = len(records) or 1
    failure_types: dict[str, int] = {}
    for r in records:
        key = r.get("failure_type") or "none"
        failure_types[key] = failure_types.get(key, 0) + 1
    return {
        "episodes": len(records),
        "subgoal_rate": sum(float(r.get("subgoal_ratio", 0.0)) for r in records) / n,
        "state_check_pass_rate": sum(1 for r in records if r.get("subgoal_checks")) / n,
        "recovery_attempts": sum(int(r.get("recovery_attempts", 0)) for r in records),
        "local_replan_success_rate": sum(1 for r in records if r.get("local_replan_success")) / n,
        "failure_type_distribution": {k: v / n for k, v in failure_types.items()},
        "safety_cost": {
            "min_human_dist": min([float(r.get("min_human_dist", 1.0)) for r in records] or [1.0]),
            "max_contact_force": max([float(r.get("max_contact_force", 0.0)) for r in records] or [0.0]),
            "emergency_stops": sum(int(r.get("emergency_stops", 0)) for r in records),
        },
    }
