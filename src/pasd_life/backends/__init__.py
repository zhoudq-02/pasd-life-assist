"""Single backend factory. Contract: docs/01 section 9 / docs/08 section 5.

    from src.pasd_life.backends import make_backend
    backend = make_backend()                     # mock by default on a fresh Linux box
    api = RobotAPI(backend)                      # RobotAPI stays the only action surface

`real` requires ALL of: PASD_BACKEND=real, PASD_ALLOW_REAL=1,
PASD_ESTOP_ACK=1 and an explicit `confirm_real=True` from the CLI.
"""
from __future__ import annotations

from typing import Any

from ..settings import Settings, load_settings
from .base import RealHardwareGuardError
from .guard import GuardConfig, GuardedBackend
from .settings_adapter import AdapterSettings

BACKENDS = ("mock", "mujoco", "real")


def make_backend(
    name: str | None = None,
    *,
    settings: Settings | None = None,
    confirm_real: bool = False,
    scene: dict | None = None,
    guard_config: GuardConfig | None = None,
) -> Any:
    s = settings or load_settings()
    backend_name = (name or s.backend).strip().lower()

    if backend_name == "mock":
        from ..robot_api import MockPiPER
        return MockPiPER(scene)   # exact scaffold semantics; no guard needed offline

    if backend_name == "mujoco":
        from .mujoco import MuJoCoBackend
        return GuardedBackend(MuJoCoBackend(), config=guard_config)

    if backend_name == "real":
        ok, missing = s.real_guard(confirm_real)
        if not ok:
            raise RealHardwareGuardError(
                "real backend refused; unmet preconditions: " + "; ".join(missing)
                + ". See docs/08 section 6."
            )
        from .piper import PiperCANBackend
        inner = PiperCANBackend(AdapterSettings.from_settings(s))
        return GuardedBackend(inner, config=guard_config)

    raise ValueError(f"unknown backend {backend_name!r}; choose from {BACKENDS}")


__all__ = ["make_backend", "BACKENDS", "GuardedBackend", "GuardConfig",
           "RealHardwareGuardError"]
