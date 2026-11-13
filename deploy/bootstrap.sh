#!/usr/bin/env bash
# One-shot bootstrap for a fresh Linux host. Contract: docs/08 section 3.
# Safe by default: zero third-party packages, backend stays "mock", no hardware
# access, no sudo, no network request unless --extras is explicitly requested.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXTRAS="none"
NO_VENV=0
OFFLINE=0
SKIP_CHECKS=0

usage() {
  cat <<'EOF'
Usage: ./deploy/bootstrap.sh [options]

  --extras LIST   pip extras to install: none|sim|robot|agent|dev|all  (default: none)
  --no-venv       use the system python3 instead of creating .venv
  --offline       never call pip (fully offline bootstrap)
  --skip-checks   only prepare the environment, do not run self-tests
  -h, --help      show this help

Examples:
  ./deploy/bootstrap.sh                       # zero-dependency, offline-capable
  ./deploy/bootstrap.sh --extras dev           # add pytest / pyyaml / ruff
  ./deploy/bootstrap.sh --extras sim,robot    # MuJoCo + PiPER SDK (needs network)
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --extras) EXTRAS="${2:-}"; shift 2 ;;
    --no-venv) NO_VENV=1; shift ;;
    --offline) OFFLINE=1; shift ;;
    --skip-checks) SKIP_CHECKS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

case "$EXTRAS" in
  *[!a-z,]*) echo "invalid --extras value: $EXTRAS" >&2; exit 2 ;;
esac
IFS=',' read -r -a EXTRA_ITEMS <<< "$EXTRAS"
for item in "${EXTRA_ITEMS[@]}"; do
  case "$item" in
    none|sim|robot|agent|dev|all) ;;
    *) echo "invalid --extras item: $item" >&2; exit 2 ;;
  esac
done

PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install Python >= 3.11 first." >&2
  exit 1
fi

"$PY" - <<'PYCHECK'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("ERROR: Python >= 3.11 required (got %s)" % sys.version.split()[0])
PYCHECK

# Linux images frequently default to LANG=C; force UTF-8 for Chinese docs/logs.
if [ -z "${LANG:-}" ] || ! printf '%s' "${LANG:-}" | grep -qi utf; then
  export LANG=C.UTF-8
  export LC_ALL=C.UTF-8
fi
export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$ROOT/src:$ROOT:$ROOT/integration${PYTHONPATH:+:$PYTHONPATH}"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[bootstrap] created .env from .env.example (edit it before real hardware)"
fi

if [ "$NO_VENV" -eq 0 ]; then
  if [ ! -d .venv ]; then
    echo "[bootstrap] creating .venv ..."
    "$PY" -m venv .venv || {
      echo "ERROR: venv creation failed. On Debian/Ubuntu: apt install python3-venv" >&2
      echo "       or rerun with --no-venv" >&2
      exit 1
    }
  fi
  PY="$ROOT/.venv/bin/python3"
fi

if [ "$EXTRAS" != "none" ] && [ "$OFFLINE" -eq 0 ]; then
  echo "[bootstrap] installing extras: $EXTRAS"
  "$PY" -m pip install --upgrade pip >/dev/null 2>&1 || true
  "$PY" -m pip install -e ".[$EXTRAS]"
elif [ "$EXTRAS" != "none" ] && [ "$OFFLINE" -eq 1 ]; then
  echo "[bootstrap] --offline: skipping pip; core self-tests need no packages"
fi

echo "[bootstrap] preparing runtime state dirs ..."
"$PY" -c 'from src.pasd_life.settings import load_settings, ensure_dirs; ensure_dirs(load_settings())'

if [ "$SKIP_CHECKS" -eq 0 ]; then
  echo "[bootstrap] environment doctor"
  "$PY" deploy/doctor.py || echo "[bootstrap] doctor reported WARN (see hints above)"
  echo "[bootstrap] contract tests"
  "$PY" scripts/contract_tests.py
  echo "[bootstrap] smoke loop"
  "$PY" scripts/run_smoke.py
  echo "[bootstrap] fairness audit"
  "$PY" scripts/fairness_audit.py
  echo "[bootstrap] backend probe"
  "$PY" scripts/run_backend_probe.py
fi

cat <<'EOF'

[bootstrap] DONE. Next steps on this Linux host:
  1) python3 deploy/doctor.py --strict     # optional: require WARN-free environment
  2) claude                               # Claude Code reads CLAUDE.md automatically
     then paste the prompt from PROMPT.md
  3) Real arm: read docs/08 section 6 FIRST. Never set PASD_BACKEND=real
     without an e-stop, a dummy head, and the three explicit confirmations.

EOF
