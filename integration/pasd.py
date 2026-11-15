"""Compatibility layer for the PASD concept document's reference implementation.

Exposes the original PASD names while delegating to src/pasd_life (single source of truth).
"""
from __future__ import annotations

from src.pasd_life.config import RETRIEVE_TOP_K
from src.pasd_life.gates import gate1_observe_failure as observe_failure  # noqa: F401
from src.pasd_life.gates import gate2_verify as verify_gate2              # noqa: F401


def retrieve_repair(library, ctx, k: int = RETRIEVE_TOP_K):
    """Original PASD name for the read point: VERIFIED/SAFE repairs for the context."""
    return library.retrieve(ctx, k)
