"""E2 protocol (docs/03 section 6). TODO(scaffold): implement.
MUST support --dry-run that prints the protocol only and NEVER emits fabricated numbers.
"""
from __future__ import annotations

import argparse


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if args.dry_run:
        print("E2: protocol only; no results generated (docs/03).")
        return
    raise NotImplementedError("TODO(scaffold): E2 implementation")


if __name__ == "__main__":
    main()
