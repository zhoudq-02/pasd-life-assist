"""Trajectory Storage: successful trajectories only, no dedup / no verification.

Table: A | proxy | requires_training=False
Contract: docs/03 section 3.
"""
from __future__ import annotations

from src.pasd_life.config import RETRIEVE_TOP_K
from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class TrajectoryStorage:
    name = "trajectory_storage"
    requires_training = False
    table = "A"

    def __init__(self, **kwargs) -> None:
        self.items: list[dict] = []   # successful trajectories only
        self.fm_calls = 0
        self.human_budget = 0
        self.extra_demos = 0
        self.verified = 0
        self.config = kwargs

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        top = self.items[-RETRIEVE_TOP_K:]
        return [
            RepairHint(text=f"trajectory:{t['task']}", executable=None, verified=False,
                       verified_by="none", source=f"trajectory#{i}")
            for i, t in enumerate(top)
        ]

    def on_episode_end(self, trace: Trace) -> None:
        if trace.success or not trace.error_code:
            self.items.append({"task": trace.task, "features": dict(trace.features)})

    def on_step_end(self, feedback: StepFeedback) -> None:
        return None  # trajectory storage has no in-episode hook

    def snapshot(self) -> dict:
        return base_snapshot(library_size=len(self.items), verified=self.verified,
                             requires_training=False,
                             human_budget=self.human_budget,
                             extra_demos=self.extra_demos, fm_calls=self.fm_calls)
