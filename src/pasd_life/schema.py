"""Core data structures. Contract: docs/01 section 2.

Do NOT rename fields or change call order. Extend only with new optional fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

STAGES_4 = ("perception", "planning", "execution", "verification")
STAGES_6 = STAGES_4 + ("interaction", "safety")
STATES = ("OBSERVED", "CANDIDATE", "VERIFIED", "SAFE", "REJECTED")
DEPLOYED_ALIAS = "SAFE"  # historical alias only; never used in logic

FEATURE_WHITELIST = frozenset({
    "aspect_ratio", "target_width", "pose_confidence", "depth_valid_ratio",
    "occlusion_ratio", "placement_error", "tilt_angle", "fill_level",
    "food_temp", "min_human_dist", "eef_speed", "contact_force",
    "intent_confidence", "gripper_width", "subgoal_idx",
})

REAL_OBSERVABLE_FIELDS = frozenset({
    "rgb", "depth", "segmentation", "pose", "joint_state", "gripper_width",
    "error_code", "aspect_ratio", "target_width", "pose_confidence",
    "depth_valid_ratio", "occlusion_ratio", "placement_error",
    "min_human_dist", "eef_speed", "contact_force", "fill_level", "food_temp",
})

VERIFY_SOURCES = ("simulation", "vlm_judge", "admission_check", "human", "none")


class PiPERError(Exception):
    """The only failure signal entering PASD."""

    def __init__(self, error_code: str, features: dict | None = None, message: str = "") -> None:
        super().__init__(message or error_code)
        self.error_code = error_code
        self.features = {k: v for k, v in (features or {}).items() if k in FEATURE_WHITELIST}
        self.message = message or error_code


@dataclass(frozen=True)
class Condition:
    """One trigger condition inside a failure signature."""
    field: str
    op: Literal[">", "<", ">=", "<=", "=="]
    theta: float

    def satisfied(self, features: dict) -> bool:
        # Hard-match gate: a missing field does NOT veto (open-world compatibility).
        if self.field not in features:
            return True
        value = features[self.field]
        if not isinstance(value, (int, float)):
            return self.op == "==" and str(value) == str(self.theta)
        return {
            ">": value > self.theta,
            "<": value < self.theta,
            ">=": value >= self.theta,
            "<=": value <= self.theta,
            "==": value == self.theta,
        }[self.op]


@dataclass(frozen=True)
class FailureSignature:
    stage: str
    error_code: str
    conditions: tuple[Condition, ...] = ()
    description: str = ""

    @property
    def is_empty(self) -> bool:
        return len(self.conditions) == 0


@dataclass
class Skill:
    """Four-element skill <sigma, C, pi, V> plus lifecycle fields."""
    sigma: FailureSignature
    applicable: dict
    repair: dict
    verification: dict
    identity: tuple[str, str, int]
    state: str = "OBSERVED"
    hits: int = 0
    tag: str = ""

    @property
    def cluster_id(self) -> int:
        return self.identity[2]


@dataclass
class Observation:
    state: dict
    success: bool = True
    steps: int = 0


@dataclass
class Trace:
    task: str
    error_code: str
    message: str
    features: dict
    scene: dict
    policy: str
    split: str = "dev"
    success: bool = False
    obs_refs: list[str] = field(default_factory=list)
    used_blocks: list[dict] = field(default_factory=list)
    candidate_blocks: list[dict] = field(default_factory=list)
    applied_repair: dict | None = None
    repair_segment: dict | None = None
    repair_verified: bool = False
    frame_id: int = 0
    elapsed: float = 0.0
    subgoal_ratio: float = 0.0

    @classmethod
    def from_error(cls, task: str, error: PiPERError, ctx: "SceneContext") -> "Trace":
        return cls(
            task=task, error_code=error.error_code, message=error.message,
            features=dict(error.features), scene=dict(ctx.features),
            policy="generated", split=ctx.split, success=False,
        )

    @classmethod
    def from_success(cls, task: str, obs: Observation, ctx: "SceneContext") -> "Trace":
        return cls(
            task=task, error_code="", message="", features=dict(ctx.features),
            scene=dict(ctx.features), policy="generated", split=ctx.split,
            success=True, elapsed=float(obs.state.get("elapsed", 0.0)),
            subgoal_ratio=float(obs.state.get("subgoal_ratio", 1.0)),
        )


@dataclass
class SceneContext:
    instruction: str
    scene_summary: str
    split: str
    features: dict
    scene_graph: Any = None


@dataclass
class StepFeedback:
    obs_before: dict
    action: dict
    obs_after: dict
    step: int


@dataclass
class RepairHint:
    """The single wrapper for every baseline output."""
    text: str
    executable: dict | None
    verified: bool
    verified_by: str
    source: str
