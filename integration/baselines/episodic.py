"""Episodic Replay: success and failure episodes replayed into the prompt.

Table: A | proxy | requires_training=False
Contract: docs/03 section 3.
TODO(scaffold): implement the mechanism-equivalent behaviour described above;
keep the MemoryPlugin signature and the six snapshot fields unchanged.
"""
from __future__ import annotations

from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class EpisodicReplay:
    name = "episodic_replay"
    requires_training = False
    table = "A"

    def __init__(self, **kwargs) -> None:
        self.items: list[dict] = []
        self.fm_calls = 0
        self.human_budget = 0
        self.extra_demos = 0
        self.verified = 0
        self.config = kwargs

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        # TODO(scaffold)
        return []

    def on_episode_end(self, trace: Trace) -> None:
        # TODO(scaffold)
        return None

    def on_step_end(self, feedback: StepFeedback) -> None:
        # TODO(scaffold) or intentionally no-op
        return None

    def snapshot(self) -> dict:
        return base_snapshot(library_size=len(self.items), verified=self.verified,
                             requires_training=False,
                             human_budget=self.human_budget,
                             extra_demos=self.extra_demos, fm_calls=self.fm_calls)
