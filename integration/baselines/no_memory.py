"""Lower bound: no memory at all (main table A)."""
from __future__ import annotations

from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class NoMemory:
    name = "no_memory"
    requires_training = False
    table = "A"

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        return []

    def on_episode_end(self, trace: Trace) -> None:
        return None

    def on_step_end(self, feedback: StepFeedback) -> None:
        return None

    def snapshot(self) -> dict:
        return base_snapshot(requires_training=False)
