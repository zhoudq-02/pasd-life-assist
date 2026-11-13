"""Batch run experiments with the shared runner (requires a runnable backend)."""
from __future__ import annotations


def main() -> None:
    raise NotImplementedError(
        "run_suite needs a runnable backend (MuJoCo/real) to run experiments non-dry; "
        "use each experiments/e*.py --dry-run for the protocol."
    )


if __name__ == "__main__":
    main()
