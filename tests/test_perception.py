"""Perception interface: YOLO/SAM/GraspNet output -> PASD observable features."""
import unittest

from src.pasd_life.perception import Detection, PerceptionResult


class TestPerception(unittest.TestCase):
    def test_no_detection_zero_confidence(self):
        r = PerceptionResult(detections=[], depth_valid_ratio=0.9, occlusion_ratio=0.0)
        self.assertEqual(r.to_features()["pose_confidence"], 0.0)

    def test_low_confidence_below_threshold(self):
        r = PerceptionResult(detections=[Detection("cup", 0.4)], depth_valid_ratio=0.9)
        self.assertEqual(r.to_features()["pose_confidence"], 0.0)

    def test_confident_detection_passthrough(self):
        r = PerceptionResult(detections=[Detection("cup", 0.9)], depth_valid_ratio=0.95)
        feats = r.to_features()
        self.assertEqual(feats["pose_confidence"], 0.9)
        self.assertEqual(feats["depth_valid_ratio"], 0.95)

    def test_occlusion_passthrough(self):
        r = PerceptionResult(detections=[Detection("cup", 0.9)], occlusion_ratio=0.8)
        self.assertEqual(r.to_features()["occlusion_ratio"], 0.8)

    def test_target_class_filter(self):
        r = PerceptionResult(detections=[Detection("cup", 0.9), Detection("box", 0.3)])
        self.assertEqual(r.best_detection("cup").class_name, "cup")
        self.assertIsNone(r.best_detection("pen"))


if __name__ == "__main__":
    unittest.main()
