"""Safety envelope (C2). Contract: docs/01 section 5 / docs/02 section 3."""
from __future__ import annotations

from dataclasses import dataclass

DEFAULT_LIMITS = {
    "min_human_dist": ("min", 0.25),     # metres
    "eef_speed": ("max", 0.15),          # m/s near the user
    "contact_force": ("max", 10.0),      # N
    "food_temp": ("max", 45.0),          # deg C
    "tilt_angle": ("max", 30.0),         # degrees
    "fill_level": ("max", 0.70),         # ratio
}

SAFETY_ERROR_CODES = frozenset({
    "MOUTH_APPROACH_UNSAFE", "FOOD_SPILL", "SAFETY_VIOLATION",
})


@dataclass(frozen=True)
class SafetyEnvelope:
    min_human_dist: float = 0.25
    max_eef_speed: float = 0.15
    max_contact_force: float = 10.0
    max_food_temp: float = 45.0
    max_tilt_angle: float = 30.0
    max_fill_level: float = 0.70

    def violated(self, features: dict) -> tuple[bool, str]:
        checks = (
            ("min_human_dist", "min", self.min_human_dist),
            ("eef_speed", "max", self.max_eef_speed),
            ("contact_force", "max", self.max_contact_force),
            ("food_temp", "max", self.max_food_temp),
            ("tilt_angle", "max", self.max_tilt_angle),
            ("fill_level", "max", self.max_fill_level),
        )
        for field, direction, limit in checks:
            if field not in features:
                continue  # missing observation is not a violation
            value = float(features[field])
            if (direction == "min" and value < limit) or (direction == "max" and value > limit):
                return True, f"{field}={value} violates {direction}={limit}"
        return False, ""

    @staticmethod
    def fallback_table() -> tuple[str, ...]:
        """Graded fallback (docs/01 section 1): never rely on LLM-generated code."""
        return ("re_perceive", "local_replan", "switch_policy", "safety_stop", "request_human")


class EmergencyStop:
    """TODO(scaffold): wire to the control-layer watchdog, NOT to the LLM."""

    def __init__(self) -> None:
        self.triggered = 0

    def trigger(self, reason: str) -> None:
        self.triggered += 1
