"""ARMADA proxy: FLOAT threshold failure detection + human takeover corrections.

Table: C2 | proxy | requires_training=True | verified_by=human
Contract: docs/03 section 3.
"""
from __future__ import annotations

from src.pasd_life.config import RETRIEVE_TOP_K
from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class ARMADAProxy:
    name = "armada"
    requires_training = True
    table = "C2"

    def __init__(self, **kwargs) -> None:
        self.items: list[dict] = []   # human-corrected segments
        self.fm_calls = 0
        self.human_budget = 0
        self.extra_demos = 0
        self.verified = 0
        self.config = kwargs

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        return [
            RepairHint(text="failure risk + fallback advice", executable=item,
                       verified=True, verified_by="human", source=f"armada#{i}")
            for i, item in enumerate(self.items[-RETRIEVE_TOP_K:])
        ]

    def on_episode_end(self, trace: Trace) -> None:
        if not (trace.success or not trace.error_code):
            self.human_budget += 1  # human takeover correction
            self.items.append({"fixes": trace.error_code, "text": "human-corrected fallback"})

    def on_step_end(self, feedback: StepFeedback) -> None:
        return None

    def snapshot(self) -> dict:
        return base_snapshot(library_size=len(self.items), verified=len(self.items),
                             requires_training=True,
                             human_budget=self.human_budget,
                             extra_demos=self.extra_demos, fm_calls=self.fm_calls)
