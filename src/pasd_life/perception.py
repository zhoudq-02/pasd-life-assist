"""Perception layer interface: map YOLO-World / SAM / GraspNet output to PASD features.

Pure code — the heavy ML stack (torch / ultralytics / open3d / graspnetAPI) feeds its
output into this interface, which produces the REAL_OBSERVABLE_FIELDS the failure
signatures consume (docs/02 §4):
  - pose_confidence    <- YOLO-World detection confidence (POSE_LOW_CONFIDENCE)
  - depth_valid_ratio  <- SAM mask + depth quality            (DETECTION_FAILED)
  - occlusion_ratio    <- SAM mask occluded fraction          (OCCLUSION_RETRIEVE_FAIL)
"""
from __future__ import annotations

from dataclasses import dataclass, field

DETECT_CONF_THRESHOLD = 0.5  # no confident detection below this


@dataclass
class Detection:
    """One YOLO-World detection."""
    class_name: str
    confidence: float
    bbox: tuple = ()  # xyxy


@dataclass
class PerceptionResult:
    """Aggregated YOLO-World + SAM + GraspNet output for one observation."""
    detections: list[Detection] = field(default_factory=list)
    depth_valid_ratio: float = 1.0   # valid depth pixels / object pixels
    occlusion_ratio: float = 0.0     # occluded fraction of the object

    def best_detection(self, target_class: str | None = None) -> Detection | None:
        cands = [d for d in self.detections
                 if target_class is None or d.class_name == target_class]
        return max(cands, key=lambda d: d.confidence) if cands else None

    def to_features(self, target_class: str | None = None) -> dict:
        """Map to the PASD observable features (fed into Extractor's SIGNATURE_RULES)."""
        det = self.best_detection(target_class)
        confident = det is not None and det.confidence >= DETECT_CONF_THRESHOLD
        return {
            "pose_confidence": det.confidence if confident else 0.0,
            "depth_valid_ratio": self.depth_valid_ratio,
            "occlusion_ratio": self.occlusion_ratio,
        }
