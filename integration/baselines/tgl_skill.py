"""Teach-and-Grow (TGL) proxy: Skill Block 7-tuple + Experience Memory 7-tuple + five admission checks.

Table: A | proxy | requires_training=False
Contract: docs/03 section 3.
verified_by = admission_check (structural, NOT simulation-quantitative — this is the
key mechanism difference from PASD's Gate2).
"""
from __future__ import annotations

from src.pasd_life.config import RETRIEVE_TOP_K
from src.pasd_life.gates import propose_repair
from src.pasd_life.schema import RepairHint, SceneContext, StepFeedback, Trace
from .base import base_snapshot


class TGLSkillMemory:
    name = "tgl_skill"
    requires_training = False
    table = "A"

    def __init__(self, **kwargs) -> None:
        self.experience: list[dict] = []    # Experience Memory: success AND failure
        self.skill_blocks: list[dict] = []  # Skill Block library: admitted blocks only
        self.verified = 0
        self.fm_calls = 0
        self.human_budget = 0
        self.extra_demos = 0
        self.config = kwargs

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        top = self.skill_blocks[:RETRIEVE_TOP_K]
        return [
            RepairHint(
                text=(b["repair"] or {}).get("text", ""),
                executable=b["repair"],
                verified=True,
                verified_by="admission_check",
                source=f"tgl_skill#{i}",
            )
            for i, b in enumerate(top)
        ]

    def on_episode_end(self, trace: Trace) -> None:
        # (1) record the episode into Experience Memory — both success and failure.
        self.experience.append({
            "task": trace.task,
            "context": dict(trace.features),
            "blocks": [],
            "outcome": "success" if (trace.success or not trace.error_code) else "failure",
            "diagnosis": trace.error_code,
            "repair": (trace.applied_repair or {}).get("text", ""),
            "evidence": dict(trace.features),
        })
        if not trace.error_code:
            return
        # (2) build a candidate Skill Block and run the five structural admission checks.
        candidate = {
            "task": trace.task,
            "diagnosis": trace.error_code,
            "repair": propose_repair(trace),
            "evidence": dict(trace.features),
        }
        if self._admit(candidate):
            candidate["state"] = "pass"
            self.skill_blocks.append(candidate)
            self.verified += 1

    def _admit(self, candidate: dict) -> bool:
        # Five structural admission checks (mechanism-equivalent, not a port):
        # 1 task present, 2 diagnosis present, 3 repair present, 4 evidence present,
        # 5 non-duplicate (task, diagnosis) identity.
        return (
            bool(candidate["task"])
            and bool(candidate["diagnosis"])
            and bool(candidate["repair"])
            and bool(candidate["evidence"])
            and not any(
                b["task"] == candidate["task"] and b["diagnosis"] == candidate["diagnosis"]
                for b in self.skill_blocks
            )
        )

    def on_step_end(self, feedback: StepFeedback) -> None:
        return None  # TGL has no in-episode memory hook

    def snapshot(self) -> dict:
        return base_snapshot(library_size=len(self.skill_blocks), verified=self.verified,
                             requires_training=False,
                             human_budget=self.human_budget,
                             extra_demos=self.extra_demos, fm_calls=self.fm_calls)
