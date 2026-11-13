"""PRAGMABOT-style STM/LTM + VLM success detector (proxy).

Table: A | proxy | requires_training=False
Contract: docs/03 section 3.
on_step_end accumulates STM reflections (VLM success detection, simulated); the
summary is written to LTM only when the episode succeeds.
"""
from __future__ import annotations

from src.pasd_life.config import RETRIEVE_TOP_K
from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class PragmabotMemory:
    name = "pragmabot"
    requires_training = False
    table = "A"

    def __init__(self, **kwargs) -> None:
        self.stm: list[dict] = []   # short-term memory: in-episode reflections
        self.ltm: list[dict] = []   # long-term memory: success summaries only
        self.fm_calls = 0
        self.human_budget = 0
        self.extra_demos = 0
        self.verified = 0
        self.config = kwargs

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        hints = [
            RepairHint(text=f"ltm:{t['task']}", executable=None, verified=False,
                       verified_by="none", source=f"ltm#{i}")
            for i, t in enumerate(self.ltm[-RETRIEVE_TOP_K:])
        ]
        hints += [
            RepairHint(text=f"stm:{r['step']}", executable=None, verified=False,
                       verified_by="none", source=f"stm#{i}")
            for i, r in enumerate(self.stm[-RETRIEVE_TOP_K:])
        ]
        return hints

    def on_step_end(self, feedback: StepFeedback) -> None:
        # VLM success detection + reflection (simulated; no real VLM in the proxy).
        self.fm_calls += 1
        self.stm.append({"step": feedback.step, "obs_after": dict(feedback.obs_after)})

    def on_episode_end(self, trace: Trace) -> None:
        if trace.success or not trace.error_code:
            self.ltm.append({"task": trace.task, "features": dict(trace.features),
                             "reflections": list(self.stm)})
        self.stm = []  # reset STM after the episode

    def snapshot(self) -> dict:
        return base_snapshot(library_size=len(self.ltm), verified=self.verified,
                             requires_training=False,
                             human_budget=self.human_budget,
                             extra_demos=self.extra_demos, fm_calls=self.fm_calls)
