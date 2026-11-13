#!/usr/bin/env python3
"""Build the self-contained Linux tarball. Runs on the PACKAGING host (any OS).

    python3 deploy/make_dist.py

Output in dist/:
    pasd-life-assist-linux-YYYYMMDD.tar.gz   (LF + UTF-8, .sh = 0755, uid/gid 1000)
    SHA256SUMS                               (verify with: sha256sum -c SHA256SUMS)
    MANIFEST.txt                             (every archived file, mode and size)

Contract: docs/08 section 2. Never archives secrets, venvs, logs or runtime state.
"""
from __future__ import annotations

import hashlib
import io
import tarfile
import time
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
TOP = "pasd-life-assist"

EXCLUDE_DIRS = {
    ".git", ".github", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".ruff_cache", ".mypy_cache", "dist", "build", "node_modules",
    "logs", "runs", "artifacts", ".doctor-tmp",
}
EXCLUDE_REL_DIRS = {"data/real"}
EXCLUDE_GLOBS = (
    "*.pyc", "*.pyo", "*.pyd", "*.egg-info", "*.key", "*.pem",
    "*.bag", "*.mcap", "*.pkl", "*.tar.gz", "*.zip",
    "integration/pasd_library_runtime.*",
    "configs/calibration.local.yaml",
    "SHA256SUMS", "MANIFEST.txt",
)
TEXT_SUFFIXES = {
    ".py", ".md", ".sh", ".yaml", ".yml", ".toml", ".json", ".txt",
    ".cfg", ".ini", ".service", ".rules", ".template", ".example",
}
TEXT_NAMES = {
    "Dockerfile", "Makefile", ".gitignore", ".gitattributes", ".dockerignore",
    ".env.example", "99-piper.rules.template", "INSTALL-LINUX.txt",
}

INSTALL_TEXT = """PASD-Life-Assist :: Linux quick start
=====================================

1) tar -xzf pasd-life-assist-linux-*.tar.gz
2) cd pasd-life-assist
3) ./deploy/bootstrap.sh          # zero third-party deps, backend stays "mock"
4) python3 deploy/doctor.py
5) make check
6) claude                        # then paste the prompt from PROMPT.md

Docs: docs/08-Linux部署与迁移.md (deployment), CLAUDE.md (agent contract).
Python >= 3.11 is required. Ubuntu 22.04 ships 3.10: use a 3.11 interpreter
or the container path (deploy/docker-compose.yml).

SAFETY: the default backend is mock and NEVER moves hardware. Real-hardware
operation requires PASD_BACKEND=real, PASD_ALLOW_REAL=1, PASD_ESTOP_ACK=1 and
an explicit CLI confirmation, plus the e-stop / dummy-head checklist in
docs/08 section 6. Never commit .env or an API key.
"""


def excluded(rel: Path, is_dir: bool) -> bool:
    parts = set(rel.parts)
    if parts & EXCLUDE_DIRS:
        return True
    posix = rel.as_posix()
    if any(posix == d or posix.startswith(d + "/") for d in EXCLUDE_REL_DIRS):
        return True
    if any(part.endswith(".egg-info") for part in rel.parts):
        return True
    for pattern in EXCLUDE_GLOBS:
        if fnmatch(rel.name, pattern) or fnmatch(posix, pattern):
            return True
    # .env is a secret; .env.example is a template and must be shipped.
    if rel.name == ".env" or (rel.name.startswith(".env.") and rel.name != ".env.example"):
        return True
    return False


def is_text(rel: Path) -> bool:
    return rel.suffix in TEXT_SUFFIXES or rel.name in TEXT_NAMES


def normalise(rel: Path, data: bytes) -> bytes:
    """Force LF and UTF-8 (BOM-free) on text files; leave binaries untouched."""
    if not is_text(rel):
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.encode("utf-8")


def collect() -> list[Path]:
    files: list[Path] = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if excluded(rel, path.is_dir()):
            continue
        if path.is_file():
            files.append(path)
    return files


def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    tar_path = DIST / f"{TOP}-linux-{stamp}.tar.gz"
    files = collect()
    dirs: set[str] = set()
    now = int(time.time())
    manifest: list[str] = []

    with tarfile.open(tar_path, "w:gz") as tf:
        for path in files:
            rel = path.relative_to(ROOT)
            arc = f"{TOP}/{rel.as_posix()}"
            # Explicit directory entries keep permissions predictable on extraction.
            parent = Path(rel).parent.as_posix()
            while parent not in (".", "") and parent not in dirs:
                dirs.add(parent)
                d = tarfile.TarInfo(f"{TOP}/{parent}")
                d.type = tarfile.DIRTYPE
                d.mode = 0o755
                d.uid = d.gid = 1000
                d.uname = d.gname = "pasd"
                d.mtime = now
                tf.addfile(d)
                parent = str(Path(parent).parent.as_posix())

            raw = normalise(rel, path.read_bytes())
            mode = 0o755 if rel.suffix == ".sh" else 0o644
            info = tarfile.TarInfo(arc)
            info.size = len(raw)
            info.mode = mode
            info.uid = info.gid = 1000
            info.uname = info.gname = "pasd"
            info.mtime = int(path.stat().st_mtime)
            tf.addfile(info, io.BytesIO(raw))
            manifest.append(f"{oct(mode)} {len(raw):>8} {rel.as_posix()}")

        install = INSTALL_TEXT.encode("utf-8")
        info = tarfile.TarInfo(f"{TOP}/INSTALL-LINUX.txt")
        info.size, info.mode, info.uid, info.gid = len(install), 0o644, 1000, 1000
        info.uname = info.gname = "pasd"
        info.mtime = now
        tf.addfile(info, io.BytesIO(install))
        manifest.append(f"{oct(0o644)} {len(install):>8} INSTALL-LINUX.txt")

    digest = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    # write_bytes (NOT write_text): on Windows, text mode would emit CRLF and
    # `sha256sum -c` on Linux would treat the trailing \r as part of the filename.
    (DIST / "SHA256SUMS").write_bytes(f"{digest}  {tar_path.name}\n".encode("utf-8"))
    header = (f"# {TOP}-linux-{stamp}.tar.gz\n"
              f"# {len(manifest)} files, LF/UTF-8 normalised, .sh=0755, uid/gid=1000\n"
              "# mode      bytes  path\n")
    (DIST / "MANIFEST.txt").write_bytes(
        (header + "\n".join(sorted(manifest)) + "\n").encode("utf-8")
    )

    print(f"Built : {tar_path}")
    print(f"Size  : {tar_path.stat().st_size:,} bytes")
    print(f"Files : {len(manifest)} (+ directory entries)")
    print(f"SHA256: {digest}")
    print("\nTransfer:")
    print(f"  scp {tar_path.name} dist/SHA256SUMS user@<linux-host>:~/")
    print("  sha256sum -c SHA256SUMS && tar -xzf *.tar.gz && cd pasd-life-assist")
    print("  ./deploy/bootstrap.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
