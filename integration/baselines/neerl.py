"""NBCagent lifelong-learning proxy: weight internalisation, anti-forgetting.

Table: C2 | proxy | requires_training=True
Differences live in the policy weights, not in an explicit experience library.
Contract: docs/03 section 3.
"""
from __future__ import annotations

from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class NEERLProxy:
    name = "neerl"
    requires_training = True
    table = "C2"

    def __init__(self, **kwargs) -> None:
        self.items: list[dict] = []   # training samples (weight-internalised)
        self.fm_calls = 0
        self.human_budget = 0
        self.extra_demos = 0
        self.verified = 0
        self.config = kwargs

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        return []  # always empty; the memory is internalised in the weights

    def on_episode_end(self, trace: Trace) -> None:
        self.items.append({"task": trace.task, "error_code": trace.error_code})

    def on_step_end(self, feedback: StepFeedback) -> None:
        return None

    def snapshot(self) -> dict:
        return base_snapshot(library_size=0, verified=0, requires_training=True,
                             human_budget=self.human_budget,
                             extra_demos=len(self.items), fm_calls=self.fm_calls)
