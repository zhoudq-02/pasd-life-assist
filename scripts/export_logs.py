"""Export unified LOG_SCHEMA traces for the paper."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pasd_life.evaluation import LOG_SCHEMA  # noqa: E402


def records_to_csv(records: list[dict], path) -> None:
    """Write records as CSV using the unified LOG_SCHEMA field order."""
    fields = list(LOG_SCHEMA)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            writer.writerow(r)


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="export LOG_SCHEMA traces")
    p.add_argument("input", nargs="?", help="JSON file of log records")
    p.add_argument("-o", "--output", default="logs.csv", help="output CSV path")
    args = p.parse_args()
    if not args.input:
        raise SystemExit("no input given; provide a JSON array of LOG_SCHEMA records")
    records = json.loads(Path(args.input).read_text(encoding="utf-8"))
    records_to_csv(records, args.output)
    print(f"wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
