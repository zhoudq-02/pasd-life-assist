"""Backend protocol and error types. Contract: docs/01 section 9 / docs/08 section 5.

A backend implements exactly `step(name, **kwargs)` and `observation()`; it is
wrapped by `RobotAPI`, which remains the ONLY whitelisted action surface.
Adding a backend must never add a control primitive.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    def step(self, name: str, **kwargs: Any) -> dict | None: ...
    def observation(self) -> dict: ...


class BackendUnavailable(RuntimeError):
    """Optional dependency, model file, or hardware adapter is not available."""


class RealHardwareGuardError(RuntimeError):
    """Raised when real-hardware preconditions are not ALL satisfied."""


class BackendGuardViolation(RuntimeError):
    """Raised by the control-layer guard before a command reaches the hardware."""
