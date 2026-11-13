"""ORIGINAL PASD: TWO gates (Gate1 + Gate2), four grasp error codes, NO Gate3.

Must stay distinct from pasd_full.py (CLAUDE.md hard constraint #6).
"""
from __future__ import annotations

from src.pasd_life.config import RETRIEVE_TOP_K
from src.pasd_life.executor import MockSimRunner
from src.pasd_life.gates import gate1_observe_failure, gate2_verify
from src.pasd_life.pasd_core import Extractor, OnlineClusterer, SkillLibrary
from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class PASDMemory:
    name = "pasd"
    requires_training = False
    table = "A"

    def __init__(self, extractor=None, clusterer=None, library=None, sim_runner=None) -> None:
        self.extractor = extractor or Extractor()
        self.clusterer = clusterer or OnlineClusterer()
        self.library = library or SkillLibrary()
        self.sim_runner = sim_runner or MockSimRunner({"aspect_ratio": 1.0})
        self.fm_calls = 0

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        skills = self.library.retrieve(ctx, RETRIEVE_TOP_K)
        return [RepairHint(s.repair.get("text", ""), s.repair, True, "simulation",
                           f"cluster#{s.cluster_id}") for s in skills]

    def on_episode_end(self, trace: Trace) -> None:
        if not trace.error_code:
            return
        self.fm_calls += 1
        candidate = gate1_observe_failure(trace, self.extractor, self.clusterer, self.library)
        if candidate is None:
            return
        if gate2_verify(candidate, self.sim_runner):
            candidate.state = "VERIFIED"
        else:
            candidate.state = "REJECTED"

    def on_step_end(self, feedback: StepFeedback) -> None:
        return None

    def snapshot(self) -> dict:
        return base_snapshot(library_size=self.library.size,
                             verified=self.library.verified_count,
                             requires_training=False, fm_calls=self.fm_calls)
