#!/usr/bin/env python3
"""Zero-dependency environment doctor for a fresh Linux host.

    python3 deploy/doctor.py            # human readable
    python3 deploy/doctor.py --json     # machine readable
    python3 deploy/doctor.py --strict   # WARN also sets exit code 1

Contract: docs/08 section 3. Never prints secret values, never writes outside
the configured PASD_HOME, never touches hardware.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.pasd_life.settings import load_settings  # noqa: E402

REQUIRED_FILES = (
    "CLAUDE.md", "README.md", "PROMPT.md", "pyproject.toml",
    "docs/00-框架总览.md", "docs/01-架构与接口契约.md", "docs/08-Linux部署与迁移.md",
    "src/pasd_life/settings.py", "src/pasd_life/backends/__init__.py",
    "scripts/contract_tests.py", "scripts/run_smoke.py", "scripts/fairness_audit.py",
    "configs/default.yaml", ".env.example",
)
OPTIONAL_MODULES = {
    "yaml": ("dev", "configs/*.yaml parsing"),
    "pytest": ("dev", "optional test discovery"),
    "ruff": ("dev", "lint"),
    "numpy": ("sim", "MuJoCo rollouts"),
    "mujoco": ("sim", "Gate2 simulation"),
    "piper_sdk": ("robot", "real PiPER arm"),
    "can": ("robot", "python-can / SocketCAN diagnostics"),
    "anthropic": ("agent", "ClaudeCodePolicyGenerator"),
}
TEXT_SUFFIXES = {".py", ".md", ".sh", ".yaml", ".yml", ".toml", ".txt",
                 ".json", ".service", ".template", ".rules"}


def _result(items: list[dict], status: str, name: str, detail: str, fix: str = "") -> None:
    items.append({"status": status, "check": name, "detail": detail, "fix": fix})


def run_checks() -> list[dict]:
    items: list[dict] = []
    s = load_settings()

    # --- interpreter & OS -------------------------------------------------
    py_ok = sys.version_info >= (3, 11)
    _result(items, "PASS" if py_ok else "FAIL", "python>=3.11",
            f"{platform.python_version()} at {sys.executable}",
            "" if py_ok else "Install Python 3.11+ (Ubuntu: apt install python3.11 python3.11-venv)")
    linux = platform.system() == "Linux"
    _result(items, "PASS" if linux else "WARN", "target OS is Linux",
            f"{platform.system()} {platform.release()} {platform.machine()}",
            "" if linux else "This repository targets Linux; local non-Linux use is packaging only.")

    # --- UTF-8 (Chinese docs/logs) ---------------------------------------
    _result(items, "PASS" if s.utf8_ok else "WARN", "UTF-8 locale",
            f"LANG={os.environ.get('LANG', '')!r} LC_ALL={os.environ.get('LC_ALL', '')!r} "
            f"fs={sys.getfilesystemencoding()}",
            "" if s.utf8_ok else "export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUTF8=1")

    # --- repository self-containment -------------------------------------
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).is_file()]
    _result(items, "PASS" if not missing else "FAIL", "repository files",
            "all required files present" if not missing else "missing: " + ", ".join(missing),
            "" if not missing else "Re-transfer the tarball; do not copy a partial directory.")

    crlf = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in {".git", ".venv", "dist", "__pycache__"} for part in path.parts):
            continue
        try:
            if b"\r\n" in path.read_bytes():
                crlf.append(str(path.relative_to(ROOT)))
        except OSError:
            continue
    _result(items, "PASS" if not crlf else "WARN", "LF line endings",
            "no CRLF found" if not crlf else f"CRLF in {len(crlf)} file(s): {', '.join(crlf[:3])}",
            "" if not crlf else "Re-extract the tarball made by deploy/make_dist.py (it normalises LF).")

    # --- dotenv & runtime state ------------------------------------------
    has_env = (ROOT / ".env").is_file()
    _result(items, "PASS" if has_env else "WARN", ".env present",
            "found" if has_env else "not found, using env vars + configs/default.yaml",
            "" if has_env else "cp .env.example .env")
    try:
        s.home.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=s.home):
            pass
        detail = f"writable: {s.home}"
        status = "PASS"
    except OSError as exc:
        detail, status = f"not writable: {s.home} ({exc})", "FAIL"
    _result(items, status, "runtime state dir", detail,
            "" if status == "PASS" else "Set PASD_HOME to a writable directory.")

    # --- optional dependencies -------------------------------------------
    for module, (extra, purpose) in OPTIONAL_MODULES.items():
        found = importlib.util.find_spec(module) is not None
        core = module in {"yaml"}
        _result(items, "PASS" if found else "WARN", f"optional module: {module}",
                "installed" if found else f"absent ({purpose})",
                "" if found else f"pip install -e '.[{extra}]'  # only when needed")
        del core

    # --- backend & hardware ----------------------------------------------
    _result(items, "PASS", "backend", f"PASD_BACKEND={s.backend} (default mock is safe)",
            "")
    if s.backend == "real":
        ok, missing_guard = s.real_guard(confirm_real=False)
        _result(items, "PASS" if not missing_guard else "WARN", "real-hardware guard",
                "all env flags set" if not missing_guard else "; ".join(missing_guard),
                "See docs/08 section 6; an explicit CLI flag is ALWAYS required too.")
        net = Path("/sys/class/net") / s.can_interface
        _result(items, "PASS" if net.is_dir() else "WARN", "SocketCAN interface",
                f"{s.can_interface}: present" if net.is_dir() else f"{s.can_interface}: absent",
                "" if net.is_dir() else "sudo ./deploy/setup_can.sh (bitrate per AgileX docs)")
        dev = Path(s.serial_device)
        _result(items, "PASS" if dev.exists() else "WARN", "serial device",
                f"{dev}: present" if dev.exists() else f"{dev}: absent",
                "" if dev.exists() else "Check lsusb/udev rule and PASD_SERIAL_DEVICE.")
        if s.adapter == "sdk":
            _result(items, "WARN", "PiPER SDK adapter",
                    "PiperSDKAdapter is an unverified skeleton",
                    "Verify the 6 SDK items in docs/08 section 6 before any motion.")
    else:
        _result(items, "PASS", "hardware guard",
                "real backend not selected; no device access attempted", "")

    # --- agent CLI --------------------------------------------------------
    claude = shutil.which("claude")
    _result(items, "PASS" if claude else "WARN", "Claude Code CLI",
            claude or "not on PATH (offline self-tests do not need it)",
            "" if claude else "npm i -g @anthropic-ai/claude-code  # Node.js >= 18")
    _result(items, "INFO", "ANTHROPIC_API_KEY",
            "set" if s.api_key_present else "not set (offline mode)",
            "" if s.api_key_present else "Only needed for ClaudeCodePolicyGenerator; keep it out of git.")

    return items


def main() -> int:
    ap = argparse.ArgumentParser(description="PASD-Life-Assist Linux environment doctor")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--strict", action="store_true", help="treat WARN as failure")
    args = ap.parse_args()

    items = run_checks()
    counts = {k: sum(1 for i in items if i["status"] == k)
              for k in ("PASS", "WARN", "FAIL", "INFO")}

    if args.json:
        print(json.dumps({"root": str(ROOT), "summary": counts, "checks": items},
                         ensure_ascii=False, indent=2))
    else:
        print("PASD-Life-Assist :: environment doctor")
        print(f"root={ROOT}  os={platform.system()}  python={platform.python_version()}")
        print("-" * 78)
        icon = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]", "INFO": "[INFO]"}
        for i in items:
            line = f"{icon[i['status']]:7} {i['check']:<28} {i['detail']}"
            print(line)
            if i["fix"] and i["status"] != "PASS":
                print(f"        -> {i['fix']}")
        print("-" * 78)
        print(f"SUMMARY: {counts['PASS']} PASS / {counts['WARN']} WARN / "
              f"{counts['FAIL']} FAIL / {counts['INFO']} INFO")

    if counts["FAIL"]:
        return 1
    if args.strict and counts["WARN"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
