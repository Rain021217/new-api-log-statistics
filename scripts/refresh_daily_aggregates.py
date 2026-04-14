#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.logging import configure_logging
from app.services.preaggregation import refresh_daily_aggregates
from app.services.source_registry import get_source_registry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh daily aggregate table for a source")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--start-date", help="YYYY-MM-DD")
    parser.add_argument("--end-date", help="YYYY-MM-DD")
    return parser.parse_args()


def to_timestamp(value: str | None, *, end_of_day: bool = False) -> int | None:
    if not value:
        return None
    suffix = "23:59:59" if end_of_day else "00:00:00"
    dt = datetime.strptime(f"{value} {suffix}", "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp())


def main() -> int:
    configure_logging()
    args = parse_args()
    registry = get_source_registry()
    source = registry.get_source(args.source_id)
    if source is None:
        raise SystemExit(f"Unknown source_id: {args.source_id}")

    result = refresh_daily_aggregates(
        source,
        start_time=to_timestamp(args.start_date),
        end_time=to_timestamp(args.end_date, end_of_day=True),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
