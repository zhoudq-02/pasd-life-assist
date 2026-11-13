"""Optional MuJoCo backend (Linux/headless). Contract: docs/01 section 9 / docs/08 section 5.

This is an ADAPTER SKELETON, not a working simulator: the PiPER MJCF model is not
shipped with the repository. It fails loudly instead of silently faking physics.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BackendUnavailable


def _require_model() -> Path:
    # repo_root = parents[2] of src/pasd_life/backends/mujoco.py
    root = Path(__file__).resolve().parents[3]
    model = root / "configs" / "mujoco" / "piper.xml"
    if not model.is_file():
        raise BackendUnavailable(
            "MuJoCo model not found: configs/mujoco/piper.xml. "
            "Provide a PiPER MJCF and friction/grip calibration "
            "(configs/calibration.yaml) before running Gate2 in simulation."
        )
    return model


class MuJoCoBackend:
    """TODO(scaffold): map the five whitelisted primitives to MuJoCo rollouts."""

    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = model_path or _require_model()
        try:
            import mujoco  # noqa: F401  # type: ignore[import-not-found]
        except ImportError as exc:
            raise BackendUnavailable(
                "mujoco is not installed. On Linux: pip install -e '.[sim]' "
                "(headless needs libgl1 / libosmesa6)."
            ) from exc
        self._model = None
        self._data = None

    def observation(self) -> dict:
        raise BackendUnavailable(
            "MuJoCoBackend.observation() TODO(scaffold): read joint/gripper state "
            "and the RGB-D stream; never expose simulation ground truth."
        )

    def step(self, name: str, **kwargs: Any) -> dict | None:
        raise BackendUnavailable(
            f"MuJoCoBackend.step({name}) TODO(scaffold): implement the primitive "
            "mapping once the MJCF model and calibration are available."
        )

    def estop(self) -> None:
        """Control-layer e-stop hook; no motion is issued by this skeleton."""
