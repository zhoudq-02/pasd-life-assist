"""Skill-Space Shooting proxy: FM judge keeps accepted repairs only. Strongest competitor.

Table: C2 | proxy | requires_training=True
This proxy does NOT perform gradient updates (the original uses DAgger) — noted in the table.
Contract: docs/03 section 3.
"""
from __future__ import annotations

from src.pasd_life.config import RETRIEVE_TOP_K
from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class SSSProxy:
    name = "sss"
    requires_training = True
    table = "C2"

    def __init__(self, **kwargs) -> None:
        self.items: list[dict] = []   # accepted repair segments only
        self.fm_calls = 0
        self.human_budget = 0
        self.extra_demos = 0
        self.verified = 0
        self.config = kwargs

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        return [
            RepairHint(text=str(item["repair"].get("text", item["repair"])),
                       executable=item["repair"], verified=True,
                       verified_by="vlm_judge", source=f"sss#{i}")
            for i, item in enumerate(self.items[-RETRIEVE_TOP_K:])
        ]

    def on_episode_end(self, trace: Trace) -> None:
        self.fm_calls += 1  # FM judge call
        if getattr(trace, "repair_verified", False):
            self.items.append({"repair": trace.applied_repair or {"fixes": trace.error_code},
                               "error_code": trace.error_code})

    def on_step_end(self, feedback: StepFeedback) -> None:
        return None

    def snapshot(self) -> dict:
        return base_snapshot(library_size=len(self.items), verified=len(self.items),
                             requires_training=True,
                             human_budget=self.human_budget,
                             extra_demos=self.extra_demos, fm_calls=self.fm_calls)
