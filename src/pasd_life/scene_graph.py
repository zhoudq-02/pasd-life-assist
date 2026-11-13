"""Shared 3D scene-graph state bus. Contract: docs/01 section 1."""
from __future__ import annotations

from dataclasses import dataclass, field


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
        # TODO(scaffold): project nodes into the whitelisted feature dict.
        return {f"pose_{k}": n.confidence for k, n in self.nodes.items()}

    def feasibility(self, action: dict) -> tuple[bool, str]:
        """TODO(scaffold): reachability / occlusion / affordance constraints for planning."""
        return True, ""
