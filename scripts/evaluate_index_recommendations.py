#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.logging import configure_logging
from app.db.source_client import execute_query, source_connection
from app.services.source_registry import get_source_registry


RECOMMENDED_INDEXES = [
    {
        "table_name": "logs",
        "index_name": "idx_logs_type_token_created_id",
        "ddl": "CREATE INDEX idx_logs_type_token_created_id ON logs(type, token_name, created_at, id)",
        "columns": ["type", "token_name", "created_at", "id"],
    },
    {
        "table_name": "logs",
        "index_name": "idx_logs_token_created_id",
        "ddl": "CREATE INDEX idx_logs_token_created_id ON logs(token_name, created_at, id)",
        "columns": ["token_name", "created_at", "id"],
    },
    {
        "table_name": "logs",
        "index_name": "idx_logs_request_id_exact",
        "ddl": "CREATE INDEX idx_logs_request_id_exact ON logs(request_id)",
        "columns": ["request_id"],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate recommended indexes for a source")
    parser.add_argument("--source-id", required=True)
    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()
    registry = get_source_registry()
    source = registry.get_source(args.source_id)
    if source is None:
        raise SystemExit(f"Unknown source_id: {args.source_id}")

    query = """
    SELECT table_name, index_name, column_name, seq_in_index
    FROM information_schema.statistics
    WHERE table_schema = %s AND table_name = 'logs'
    ORDER BY table_name, index_name, seq_in_index
    """
    with source_connection(source) as conn:
        with conn.cursor() as cursor:
            execute_query(
                cursor,
                query,
                (source.database,),
                source_id=source.source_id,
                query_name="evaluate_index_recommendations",
            )
            rows = cursor.fetchall() or []

    existing = {}
    for row in rows:
        existing.setdefault(row["index_name"], []).append(row["column_name"])

    result = []
    for candidate in RECOMMENDED_INDEXES:
        exists = any(cols == candidate["columns"] for cols in existing.values())
        result.append(
            {
                **candidate,
                "already_present": exists,
            }
        )

    print(
        json.dumps(
            {
                "source_id": source.source_id,
                "recommended_indexes": result,
                "existing_indexes": existing,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
