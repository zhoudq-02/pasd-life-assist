"""Linux-first runtime settings (stdlib only). Contract: docs/01 section 9 / docs/08.

Priority: environment variables (PASD_*) > configs/default.yaml (optional PyYAML)
> built-in defaults. No absolute host path, no secret in logs, no network access.
"""
from __future__ import annotations

import locale
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

VALID_BACKENDS = ("mock", "mujoco", "real")
VALID_SPLITS = ("dev", "heldout")
VALID_ADAPTERS = ("sdk", "null")


def repo_root() -> Path:
    """Repository root, resolved at runtime. Never hard-code a machine path."""
    return Path(__file__).resolve().parents[2]


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _load_dotenv(path: Path) -> None:
    """Minimal, side-effect-free .env reader. Never evaluates shell code.

    Existing environment variables win, so `PASD_BACKEND=mock python3 ...` overrides .env.
    """
    if not path.is_file():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        else:
            value = value.split("#", 1)[0].strip()
        if key and key not in os.environ:
            os.environ[key] = value


def _read_yaml(path: Path) -> dict[str, Any]:
    """PyYAML is optional; on a bare Linux box the defaults must still work."""
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 - malformed/undecodable config falls back to defaults
        return {}
    return data if isinstance(data, dict) else {}


def _utf8_ok() -> bool:
    """A fresh Linux host often boots with LANG=C; Chinese logs would break there."""
    def norm(value: str) -> str:
        return str(value).lower().replace("-", "").replace("_", "")

    fs = norm(sys.getfilesystemencoding()).startswith("utf8")
    pref = norm(locale.getpreferredencoding(False)).startswith("utf8")
    env_lang = norm(os.environ.get("LANG") or os.environ.get("LC_ALL") or "")
    return fs and pref and ("utf" in env_lang or env_lang == "")


@dataclass(frozen=True)
class Settings:
    backend: str
    split: str
    seed: int
    repo: Path
    home: Path
    log_dir: Path
    run_dir: Path
    artifact_dir: Path
    can_interface: str
    can_bitrate: int
    serial_device: str
    llm_model: str
    adapter: str
    allow_real: bool
    estop_ack: bool
    api_key_present: bool
    utf8_ok: bool

    def real_guard(self, confirm_real: bool) -> tuple[bool, list[str]]:
        """Three independent confirmations before any real hardware can move."""
        missing: list[str] = []
        if self.backend != "real":
            missing.append("backend is not 'real'")
        if not self.allow_real:
            missing.append("PASD_ALLOW_REAL is not 1")
        if not self.estop_ack:
            missing.append("PASD_ESTOP_ACK is not 1 (hardware e-stop not acknowledged)")
        if not confirm_real:
            missing.append("explicit CLI confirmation flag is missing")
        return (not missing), missing

    def describe(self) -> dict[str, Any]:
        """Safe to print: never includes the API key value."""
        d = asdict(self)
        for k, v in list(d.items()):
            if isinstance(v, Path):
                d[k] = str(v)
        d["api_key_present"] = self.api_key_present
        return d


def load_settings(*, load_dotenv: bool = True) -> Settings:
    repo = repo_root()
    if load_dotenv:
        _load_dotenv(repo / ".env")
    cfg = _read_yaml(repo / "configs" / "default.yaml")
    platform_cfg = cfg.get("platform", {}) if isinstance(cfg.get("platform"), dict) else {}

    backend = os.environ.get("PASD_BACKEND") or str(platform_cfg.get("backend", "mock"))
    backend = backend.strip().lower()
    if backend not in VALID_BACKENDS:
        raise ValueError(f"PASD_BACKEND must be one of {VALID_BACKENDS}, got {backend!r}")

    split = os.environ.get("PASD_SPLIT") or str(cfg.get("split", "dev"))
    split = split.strip().lower()
    if split not in VALID_SPLITS:
        raise ValueError(f"PASD_SPLIT must be one of {VALID_SPLITS}, got {split!r}")

    adapter = os.environ.get("PASD_ADAPTER", "sdk").strip().lower()
    if adapter not in VALID_ADAPTERS:
        raise ValueError(f"PASD_ADAPTER must be one of {VALID_ADAPTERS}, got {adapter!r}")

    try:
        seed = int(os.environ.get("PASD_SEED", cfg.get("seed", 0)))
    except (TypeError, ValueError):
        seed = 0

    home_env = os.environ.get("PASD_HOME")
    if home_env:
        home = Path(home_env).expanduser()
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
        home = base / "pasd-life-assist"
    home = home.resolve()

    try:
        bitrate = int(os.environ.get("PASD_CAN_BITRATE", "1000000"))
    except ValueError:
        bitrate = 1000000

    return Settings(
        backend=backend,
        split=split,
        seed=seed,
        repo=repo,
        home=home,
        log_dir=home / "logs",
        run_dir=home / "runs",
        artifact_dir=home / "artifacts",
        can_interface=os.environ.get("PASD_CAN_INTERFACE", "can0"),
        can_bitrate=bitrate,
        serial_device=os.environ.get("PASD_SERIAL_DEVICE", "/dev/ttyUSB0"),
        llm_model=os.environ.get("PASD_LLM_MODEL", ""),
        adapter=adapter,
        allow_real=_truthy(os.environ.get("PASD_ALLOW_REAL")),
        estop_ack=_truthy(os.environ.get("PASD_ESTOP_ACK")),
        api_key_present=bool(os.environ.get("ANTHROPIC_API_KEY")),
        utf8_ok=_utf8_ok(),
    )


def ensure_dirs(s: Settings) -> None:
    """Create runtime state directories. Called by bootstrap, never at import time."""
    for path in (s.home, s.log_dir, s.run_dir, s.artifact_dir):
        path.mkdir(parents=True, exist_ok=True)
