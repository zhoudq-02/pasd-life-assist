"""IROSA interface comparison ONLY (validated parameterized KMP tools + protective layer).

Table: C1 | proxy | requires_training=False | excluded from the SR main table
Contract: docs/03 section 3.
"""
from __future__ import annotations

from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot

KMP_TOOLS = ("insert", "peg_in_hole", "screw", "place")


class IROSAInterface:
    name = "irosa_interface"
    requires_training = False
    table = "C1"

    def __init__(self, **kwargs) -> None:
        self.items: list[dict] = []
        self.fm_calls = 0
        self.human_budget = 0
        self.extra_demos = 0
        self.verified = 0
        self.config = kwargs

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        # Interface comparison only: expose the validated, parameterized KMP tools.
        return [RepairHint(text=f"validated KMP tools: {', '.join(KMP_TOOLS)}",
                           executable=None, verified=True, verified_by="none",
                           source="irosa_interface")]

    def on_episode_end(self, trace: Trace) -> None:
        return None  # interface-only: no experience memory

    def on_step_end(self, feedback: StepFeedback) -> None:
        return None

    def snapshot(self) -> dict:
        return base_snapshot(library_size=0, verified=0, requires_training=False,
                             human_budget=self.human_budget,
                             extra_demos=self.extra_demos, fm_calls=self.fm_calls)
