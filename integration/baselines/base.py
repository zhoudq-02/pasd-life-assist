"""MemoryPlugin unified adapter (v1.1). Contract: docs/01 section 8 / docs/03."""
from __future__ import annotations

from typing import Protocol

from src.pasd_life.config import SNAPSHOT_FIELDS
from src.pasd_life.schema import RepairHint, StepFeedback, Trace, SceneContext


class MemoryPlugin(Protocol):
    name: str

    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        """The only memory read point before planning."""

    def on_episode_end(self, trace: Trace) -> None:
        """The only persistence write point."""

    def on_step_end(self, feedback: StepFeedback) -> None:
        """Optional in-episode hook; default no-op. Every baseline MUST implement it."""

    def snapshot(self) -> dict:
        """Must contain the six SNAPSHOT_FIELDS for fairness auditing."""


def check_snapshot(snapshot: dict) -> None:
    missing = [k for k in SNAPSHOT_FIELDS if k not in snapshot]
    if missing:
        raise ValueError(f"snapshot() missing fields: {missing}")


def base_snapshot(*, library_size: int = 0, verified: int = 0,
                  requires_training: bool = False, human_budget: int = 0,
                  extra_demos: int = 0, fm_calls: int = 0) -> dict:
    return {
        "library_size": library_size, "verified": verified,
        "requires_training": requires_training, "human_budget": human_budget,
        "extra_demos": extra_demos, "fm_calls": fm_calls,
    }
