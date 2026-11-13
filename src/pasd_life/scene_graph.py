"""Shared 3D scene-graph state bus. Contract: docs/01 section 1."""
from __future__ import annotations

from dataclasses import dataclass, field

from .schema import REAL_OBSERVABLE_FIELDS


@dataclass
class SceneNode:
    object_id: str
    pose: tuple
    affordance: str = ""
    confidence: float = 1.0
    timestamp: float = 0.0


@dataclass
class SceneGraph:
    nodes: dict[str, SceneNode] = field(default_factory=dict)
    frame_id: int = 0

    def upsert(self, node: SceneNode) -> None:
        self.nodes[node.object_id] = node

    def observable_features(self) -> dict:
        """Project nodes into whitelisted observable fields (anti-contamination)."""
        features: dict = {}
        if self.nodes:
            features["pose_confidence"] = min(n.confidence for n in self.nodes.values())
        return {k: v for k, v in features.items() if k in REAL_OBSERVABLE_FIELDS}

    def feasibility(self, action: dict) -> tuple[bool, str]:
        """Reachability / affordance precheck for planning (docs/01 section 1)."""
        target = action.get("target_object") or action.get("target")
        if target and target not in self.nodes:
            return False, f"target '{target}' not in scene graph"
        affordance = action.get("affordance")
        if target and affordance and self.nodes[target].affordance != affordance:
            return False, f"affordance mismatch: {self.nodes[target].affordance} != {affordance}"
        return True, ""
