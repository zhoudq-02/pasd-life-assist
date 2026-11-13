"""Six ablation switches for main table B (docs/03 section 2)."""
from __future__ import annotations

ABLATIONS = (
    "no_gate1", "no_gate2", "no_gate3", "no_task_level_signature",
    "no_directional_rounding", "no_eval_driven_randomisation",
)


def build_ablation(name: str, **kwargs):
    """TODO(scaffold): clone PASDFullMemory and disable exactly one component."""
    if name not in ABLATIONS:
        raise KeyError(name)
    raise NotImplementedError("TODO(scaffold)")
