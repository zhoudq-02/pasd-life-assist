"""Compatibility layer for the PASD concept document's reference implementation."""
# TODO(scaffold): expose observe_failure / verify_gate2 / retrieve_repair under the
# original names while delegating to src/pasd_life (single source of truth).
from src.pasd_life.gates import gate1_observe_failure as observe_failure  # noqa: F401
from src.pasd_life.gates import gate2_verify as verify_gate2              # noqa: F401
