"""Single source of truth for thresholds. Never hard-code numbers in business code."""
from __future__ import annotations

CLUSTER_RADIUS = 0.45
GATE2_REPEATS = 10
GATE2_THRESHOLD = 0.80
GATE3_CONSECUTIVE = 8
GATE3_REQUIRES_HUMAN_CONFIRM = True

INTENT_CONF_THRESHOLD = 0.6
POSE_CONF_THRESHOLD = 0.6
ASPECT_RATIO_SLIP = 4.0
MAX_GRIPPER_WIDTH = 0.070            # metres, PiPER two-finger range 0-70 mm
MAX_STEPS = 30
RETRIEVE_TOP_K = 3

LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 2048
LLM_MODEL_DEFAULT = "deepseek-v4-pro[1M]"

EPISODES_PER_METHOD = 200
INSTRUCTION_COUNTS = {"simple": 7, "implicit": 4, "composed": 13}
ROUNDS_PER_INSTRUCTION = 50

E1_FAILURES = 240
E1_CLUSTERS = 9
E1_PURITY = 1.0
E1_DEDUP_RATE = 0.96
E2_FTR_RANGE = (0.15, 0.26)

SNAPSHOT_FIELDS = (
    "library_size", "verified", "requires_training",
    "human_budget", "extra_demos", "fm_calls",
)
