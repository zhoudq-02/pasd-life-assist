"""Baseline registry. Adding a baseline requires syncing configs/baselines.yaml + docs/06."""
from __future__ import annotations

import importlib

from .base import MemoryPlugin

# name -> (module, class, table, requires_training)
REGISTRY: dict[str, tuple[str, str, str, bool]] = {
    "no_memory": ("no_memory", "NoMemory", "A", False),
    "trajectory_storage": ("trajectory", "TrajectoryStorage", "A", False),
    "episodic_replay": ("episodic", "EpisodicReplay", "A", False),
    "pasd": ("pasd", "PASDMemory", "A", False),
    "pragmabot": ("pragmabot", "PragmabotMemory", "A", False),
    "tgl_skill": ("tgl_skill", "TGLSkillMemory", "A", False),
    "pasd_full": ("pasd_full", "PASDFullMemory", "A", False),
    "reflexion": ("reflexion", "ReflexionMemory", "C1", False),
    "uniskill_proxy": ("uniskill_proxy", "UniskillProxy", "C1", False),
    "irosa_interface": ("irosa_interface", "IROSAInterface", "C1", False),
    "sss": ("sss", "SSSProxy", "C2", True),
    "soar": ("soar", "SOARProxy", "C2", True),
    "armada": ("armada", "ARMADAProxy", "C2", True),
    "neerl": ("neerl", "NEERLProxy", "C2", True),
    "rlingua": ("rlingua", "RLinguaProxy", "C2", True),
    "vla_proxy": ("vla_proxy", "VLAProxy", "C2", True),
}


def build(name: str, **kwargs) -> MemoryPlugin:
    if name not in REGISTRY:
        raise KeyError(f"unknown baseline: {name}")
    module_name, class_name, _, _ = REGISTRY[name]
    module = importlib.import_module(f"integration.baselines.{module_name}")
    return getattr(module, class_name)(**kwargs)


def list_baselines(table: str | None = None) -> list[str]:
    return [n for n, (_, _, t, _) in REGISTRY.items() if table is None or t == table]
