"""THIS SYSTEM: three gates + task-level signature extension + safety envelope (C1/C2)."""
from __future__ import annotations

from src.pasd_life.config import RETRIEVE_TOP_K
from src.pasd_life.executor import MockSimRunner
from src.pasd_life.gates import gate1_observe_failure, promote
from src.pasd_life.pasd_core import Extractor, OnlineClusterer, SkillLibrary
from src.pasd_life.safety import SafetyEnvelope
from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class PASDFullMemory:
    name = "pasd_full"
    requires_training = False
    table = "A"

    def __init__(self, extractor=None, clusterer=None, library=None,
                 sim_runner=None, envelope=None, human_confirmed: bool = False) -> None:
        self.extractor = extractor or Extractor()
        self.clusterer = clusterer or OnlineClusterer()
        self.library = library or SkillLibrary()
        self.sim_runner = sim_runner or MockSimRunner({"aspect_ratio": 1.0})
        self.envelope = envelope or SafetyEnvelope()
        self.human_confirmed = human_confirmed
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
        promote(candidate, sim_runner=self.sim_runner, features=trace.features,
                envelope=self.envelope, human_confirmed=self.human_confirmed)

    def on_step_end(self, feedback: StepFeedback) -> None:
        return None  # PASD has no in-episode memory hook

    def snapshot(self) -> dict:
        return base_snapshot(library_size=self.library.size,
                             verified=self.library.verified_count,
                             requires_training=False,
                             human_budget=int(self.human_confirmed),
                             fm_calls=self.fm_calls)
