"""Extractor / OnlineClusterer / SkillLibrary / Retriever. Contract: docs/01 section 4."""
from __future__ import annotations

import math
import pickle
from pathlib import Path

from .config import CLUSTER_RADIUS, RETRIEVE_TOP_K
from .schema import Condition, FailureSignature, SceneContext, Skill, FEATURE_WHITELIST

# error_code -> ((feature, operator), ...) ; only whitelisted diagnostic features
SIGNATURE_RULES: dict[str, tuple[tuple[str, str], ...]] = {
    "GRASP_SLIP": (("aspect_ratio", ">"),),
    "GRASP_IMPOSSIBLE": (("target_width", ">"),),
    "IK_UNREACHABLE": (),                       # non-repairable, empty signature
    "POSE_LOW_CONFIDENCE": (("pose_confidence", "<"),),
    "DETECTION_FAILED": (("depth_valid_ratio", "<"),),
    "OCCLUSION_RETRIEVE_FAIL": (("occlusion_ratio", ">"),),
    "PLACEMENT_OFFSET": (("placement_error", ">"),),
    "FOOD_SPILL": (("tilt_angle", ">"), ("fill_level", ">")),
    "MOUTH_APPROACH_UNSAFE": (("min_human_dist", "<"), ("eef_speed", ">")),
    "INTENT_AMBIGUOUS": (("intent_confidence", "<"),),
    "SAFETY_VIOLATION": (("min_human_dist", "<"), ("contact_force", ">")),
}

STAGE_BY_ERROR: dict[str, str] = {
    "GRASP_SLIP": "execution", "GRASP_IMPOSSIBLE": "execution",
    "IK_UNREACHABLE": "planning", "POSE_LOW_CONFIDENCE": "perception",
    "DETECTION_FAILED": "perception", "OCCLUSION_RETRIEVE_FAIL": "perception",
    "PLACEMENT_OFFSET": "verification", "FOOD_SPILL": "execution",
    "MOUTH_APPROACH_UNSAFE": "safety", "INTENT_AMBIGUOUS": "interaction",
    "SAFETY_VIOLATION": "safety",
}


class Extractor:
    """Thresholds come ONLY from trace.features; trace.scene is for clustering only."""

    @staticmethod
    def q_dir(value: float, op: str) -> float:
        """Directional rounding (fixes defect D9): '>' rounds down, '<' rounds up."""
        if op in (">", ">="):
            return float(math.floor(value))
        if op in ("<", "<="):
            return float(math.ceil(value))
        return float(value)

    def extract(self, trace, strategy: str = "margin") -> FailureSignature:
        stage = STAGE_BY_ERROR.get(trace.error_code, "execution")
        conditions: list[Condition] = []
        for feat, op in SIGNATURE_RULES.get(trace.error_code, ()):
            if feat not in trace.features or feat not in FEATURE_WHITELIST:
                continue
            value = trace.features[feat]
            if not isinstance(value, (int, float)):
                continue
            theta = self.q_dir(float(value), op) if strategy in ("margin", "quantized") else float(value)
            if strategy == "split" and op == ">" and float(value) < 0.6:
                continue  # TODO(scaffold): real AUC-based dimension pruning
            conditions.append(Condition(feat, op, theta))
        return FailureSignature(stage, trace.error_code, tuple(conditions), trace.message)


class OnlineClusterer:
    """Streaming clustering, amortised O(1) insertion. Identity = (stage, error_code, cluster_id)."""

    def __init__(self, radius: float = CLUSTER_RADIUS) -> None:
        self.radius = radius
        self._centers: dict[tuple[str, str], list[list[float]]] = {}

    @staticmethod
    def _vector(signature: FailureSignature) -> list[float]:
        return [c.theta for c in signature.conditions] or [0.0]

    @staticmethod
    def _dist(a: list[float], b: list[float]) -> float:
        n = max(len(a), len(b))
        aa = list(a) + [0.0] * (n - len(a))
        bb = list(b) + [0.0] * (n - len(b))
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(aa, bb))) / math.sqrt(n)

    def assign(self, signature: FailureSignature, scene: dict | None = None) -> int:
        key = (signature.stage, signature.error_code)
        centers = self._centers.setdefault(key, [])
        vec = self._vector(signature)
        for cid, center in enumerate(centers):
            if self._dist(vec, center) <= self.radius:
                for i in range(min(len(vec), len(center))):
                    center[i] = (center[i] + vec[i]) / 2.0
                return cid
        centers.append(list(vec))
        return len(centers) - 1

    @property
    def cluster_count(self) -> int:
        return sum(len(v) for v in self._centers.values())


class Retriever:
    @staticmethod
    def matches(signature: FailureSignature, features: dict) -> bool:
        if signature.is_empty:
            return False  # never allow a "universal skill"
        return all(c.satisfied(features) for c in signature.conditions)


class SkillLibrary:
    def __init__(self) -> None:
        self._skills: dict[tuple[str, str, int], Skill] = {}

    def ingest(self, skill: Skill) -> None:
        self._skills[skill.identity] = skill

    def get(self, identity: tuple[str, str, int]) -> Skill | None:
        return self._skills.get(identity)

    def retrieve(self, ctx: SceneContext, k: int = RETRIEVE_TOP_K) -> list[Skill]:
        matched = [s for s in self._skills.values()
                   if s.state in ("VERIFIED", "SAFE") and Retriever.matches(s.sigma, ctx.features)]
        matched.sort(key=lambda s: s.hits, reverse=True)
        return matched[:k]

    def all(self) -> list[Skill]:
        return list(self._skills.values())

    @property
    def size(self) -> int:
        """|B_t| -- the measured quantity of C1's convergence curve."""
        return len(self._skills)

    @property
    def verified_count(self) -> int:
        return sum(1 for s in self._skills.values() if s.state in ("VERIFIED", "SAFE"))

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(pickle.dumps({"skills": self._skills}))

    @classmethod
    def load(cls, path: str | Path) -> "SkillLibrary":
        lib = cls()
        data = pickle.loads(Path(path).read_bytes())
        for key, skill in data.get("skills", {}).items():
            lib._skills[key] = skill
        return lib
