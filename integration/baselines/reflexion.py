"""Pure Reflexion lower bound: last-k natural-language lessons, no RAG/success detector.

Table: C1 | proxy | requires_training=False
Contract: docs/03 section 3.
"""
from __future__ import annotations

from src.pasd_life.config import RETRIEVE_TOP_K
from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class ReflexionMemory:
    name = "reflexion"
    requires_training = False
    table = "C1"

    def __init__(self, **kwargs) -> None:
        self.items: list[dict] = []   # natural-language lessons
        self.fm_calls = 0
        self.human_budget = 0
        self.extra_demos = 0
        self.verified = 0
        self.config = kwargs

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        return [
            RepairHint(text=lesson["text"], executable=None, verified=False,
                       verified_by="none", source=f"reflexion#{i}")
            for i, lesson in enumerate(self.items[-RETRIEVE_TOP_K:])
        ]

    def on_episode_end(self, trace: Trace) -> None:
        outcome = "success" if (trace.success or not trace.error_code) else trace.error_code
        self.items.append({"text": f"{trace.task}: {outcome}"})

    def on_step_end(self, feedback: StepFeedback) -> None:
        return None  # pure Reflexion has no in-episode success detector

    def snapshot(self) -> dict:
        return base_snapshot(library_size=len(self.items), verified=self.verified,
                             requires_training=False,
                             human_budget=self.human_budget,
                             extra_demos=self.extra_demos, fm_calls=self.fm_calls)
