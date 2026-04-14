from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.db.source_client import execute_query, source_connection
from app.schemas.source import SourceDefinition


DAILY_AGG_TABLE = "log_daily_aggregates"


def ensure_daily_aggregate_table(source: SourceDefinition) -> None:
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {DAILY_AGG_TABLE} (
      agg_date DATE NOT NULL,
      token_name VARCHAR(128) NOT NULL DEFAULT '',
      model_name VARCHAR(128) NOT NULL DEFAULT '',
      username VARCHAR(64) NOT NULL DEFAULT '',
      group_name VARCHAR(64) NOT NULL DEFAULT '',
      channel_id INT NOT NULL DEFAULT 0,
      request_path VARCHAR(255) NOT NULL DEFAULT '',
      request_count BIGINT NOT NULL DEFAULT 0,
      quota_total DECIMAL(36, 12) NOT NULL DEFAULT 0,
      actual_cost_total DECIMAL(36, 12) NOT NULL DEFAULT 0,
      input_tokens_total BIGINT NOT NULL DEFAULT 0,
      input_cost_total DECIMAL(36, 12) NOT NULL DEFAULT 0,
      output_tokens_total BIGINT NOT NULL DEFAULT 0,
      output_cost_total DECIMAL(36, 12) NOT NULL DEFAULT 0,
      cache_read_tokens_total BIGINT NOT NULL DEFAULT 0,
      cache_read_cost_total DECIMAL(36, 12) NOT NULL DEFAULT 0,
      cache_saving_total DECIMAL(36, 12) NOT NULL DEFAULT 0,
      cache_write_tokens_total BIGINT NOT NULL DEFAULT 0,
      cache_write_cost_total DECIMAL(36, 12) NOT NULL DEFAULT 0,
      fixed_cost_total DECIMAL(36, 12) NOT NULL DEFAULT 0,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (agg_date, token_name, model_name, username, group_name, channel_id, request_path),
      KEY idx_agg_token_date (token_name, agg_date),
      KEY idx_agg_model_date (model_name, agg_date),
      KEY idx_agg_group_date (group_name, agg_date),
      KEY idx_agg_channel_date (channel_id, agg_date)
    )
    """
    settings = get_settings()
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            execute_query(
                cursor,
                ddl,
                source_id=source.source_id,
                query_name="ensure_daily_aggregate_table",
            )


def has_daily_aggregate_table(source: SourceDefinition) -> bool:
    query = """
    SELECT COUNT(*) AS c
    FROM information_schema.tables
    WHERE table_schema = %s AND table_name = %s
    """
    settings = get_settings()
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            execute_query(
                cursor,
                query,
                (source.database, DAILY_AGG_TABLE),
                source_id=source.source_id,
                query_name="has_daily_aggregate_table",
            )
            row = cursor.fetchone() or {}
    return int(row.get("c") or 0) > 0


def refresh_daily_aggregates(
    source: SourceDefinition,
    *,
    start_time: int | None = None,
    end_time: int | None = None,
) -> dict[str, Any]:
    ensure_daily_aggregate_table(source)

    where_parts = ["l.type = 2"]
    params: list[Any] = []
    if start_time:
      where_parts.append("l.created_at >= %s")
      params.append(start_time)
    if end_time:
      where_parts.append("l.created_at <= %s")
      params.append(end_time)
    where_sql = " AND ".join(where_parts)

    delete_sql = f"DELETE FROM {DAILY_AGG_TABLE}"
    if start_time or end_time:
        date_parts = []
        delete_params: list[Any] = []
        if start_time:
            date_parts.append("agg_date >= DATE(FROM_UNIXTIME(%s))")
            delete_params.append(start_time)
        if end_time:
            date_parts.append("agg_date <= DATE(FROM_UNIXTIME(%s))")
            delete_params.append(end_time)
        delete_sql += " WHERE " + " AND ".join(date_parts)
    else:
        delete_params = []

    insert_sql = f"""
    INSERT INTO {DAILY_AGG_TABLE} (
      agg_date,
      token_name,
      model_name,
      username,
      group_name,
      channel_id,
      request_path,
      request_count,
      quota_total,
      actual_cost_total,
      input_tokens_total,
      input_cost_total,
      output_tokens_total,
      output_cost_total,
      cache_read_tokens_total,
      cache_read_cost_total,
      cache_saving_total,
      cache_write_tokens_total,
      cache_write_cost_total,
      fixed_cost_total
    )
    WITH sys AS (
      SELECT
        (
          CASE
            WHEN MAX(CASE WHEN `key` = 'general_setting.quota_display_type' THEN `value` END) = 'CNY'
            THEN COALESCE(MAX(CASE WHEN `key` = 'USDExchangeRate' THEN CAST(`value` AS DECIMAL(20,6)) END), 7.0)
            WHEN MAX(CASE WHEN `key` = 'general_setting.quota_display_type' THEN `value` END) = 'CUSTOM'
            THEN COALESCE(MAX(CASE WHEN `key` = 'general_setting.custom_currency_exchange_rate' THEN CAST(`value` AS DECIMAL(20,6)) END), 1.0)
            ELSE 1.0
          END
          /
          COALESCE(MAX(CASE WHEN `key` = 'QuotaPerUnit' THEN CAST(`value` AS DECIMAL(20,6)) END), 500000)
        ) AS cost_factor,
        COALESCE(MAX(CASE WHEN `key` = 'QuotaPerUnit' THEN CAST(`value` AS DECIMAL(20,6)) END), 500000) AS sys_quota_per_unit
      FROM options
    ),
    raw AS (
      SELECT
        DATE(FROM_UNIXTIME(l.created_at)) AS agg_date,
        l.username,
        l.token_name,
        l.model_name,
        l.quota,
        l.prompt_tokens,
        l.completion_tokens,
        l.channel_id,
        l.`group`,
        JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.request_path')) AS request_path,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.cache_tokens')), '0') AS UNSIGNED) AS cache_tokens,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.cache_creation_tokens')), '0') AS UNSIGNED) AS cache_creation_tokens,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.cache_creation_tokens_5m')), '0') AS UNSIGNED) AS cache_creation_tokens_5m,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.cache_creation_tokens_1h')), '0') AS UNSIGNED) AS cache_creation_tokens_1h,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.model_ratio')), '0') AS DECIMAL(20,6)) AS r_model,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.completion_ratio')), '0') AS DECIMAL(20,6)) AS r_comp,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.cache_ratio')), '0') AS DECIMAL(20,6)) AS r_cache,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.cache_creation_ratio')), '0') AS DECIMAL(20,6)) AS r_cache_create,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.cache_creation_ratio_5m')), '0') AS DECIMAL(20,6)) AS r_cache_create_5m,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.cache_creation_ratio_1h')), '0') AS DECIMAL(20,6)) AS r_cache_create_1h,
        CAST(COALESCE(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.model_price')), '0') AS DECIMAL(20,6)) AS r_price,
        CAST(
          COALESCE(
            NULLIF(JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.user_group_ratio')), '-1'),
            JSON_UNQUOTE(JSON_EXTRACT(l.other, '$.group_ratio')),
            '1'
          ) AS DECIMAL(20,6)
        ) AS r_group
      FROM logs l
      WHERE {where_sql}
    ),
    cost_detail AS (
      SELECT
        raw.agg_date,
        raw.username,
        raw.token_name,
        raw.model_name,
        raw.channel_id,
        raw.`group`,
        COALESCE(NULLIF(raw.request_path, ''), '[空路径]') AS request_path,
        raw.quota,
        raw.completion_tokens,
        raw.cache_tokens,
        (
          CASE
            WHEN raw.cache_creation_tokens_5m + raw.cache_creation_tokens_1h > 0
            THEN raw.cache_creation_tokens_5m + raw.cache_creation_tokens_1h
            ELSE raw.cache_creation_tokens
          END
        ) AS cache_write_tokens_total,
        GREATEST(
          0,
          CAST(raw.prompt_tokens AS SIGNED) - CAST(raw.cache_tokens AS SIGNED) -
          CAST(
            CASE
              WHEN raw.cache_creation_tokens_5m + raw.cache_creation_tokens_1h > 0
              THEN raw.cache_creation_tokens_5m + raw.cache_creation_tokens_1h
              ELSE raw.cache_creation_tokens
            END AS SIGNED
          )
        ) AS pure_prompt_tokens,
        (raw.quota * sys.cost_factor) AS cost_total,
        IF(raw.r_price > 0, 0,
          GREATEST(
            0,
            CAST(raw.prompt_tokens AS SIGNED) - CAST(raw.cache_tokens AS SIGNED) -
            CAST(
              CASE
                WHEN raw.cache_creation_tokens_5m + raw.cache_creation_tokens_1h > 0
                THEN raw.cache_creation_tokens_5m + raw.cache_creation_tokens_1h
                ELSE raw.cache_creation_tokens
              END AS SIGNED
            )
          ) * raw.r_model * raw.r_group * sys.cost_factor
        ) AS cost_input,
        IF(raw.r_price > 0, 0,
          raw.completion_tokens * raw.r_model * raw.r_comp * raw.r_group * sys.cost_factor
        ) AS cost_output,
        IF(raw.r_price > 0, 0,
          raw.cache_tokens * raw.r_model * raw.r_cache * raw.r_group * sys.cost_factor
        ) AS cost_cache_read,
        IF(raw.r_price > 0, 0,
          GREATEST(
            0,
            raw.cache_tokens * raw.r_model * raw.r_group * sys.cost_factor * (1 - raw.r_cache)
          )
        ) AS cost_cache_saving,
        IF(raw.r_price > 0, 0,
          (
            CASE
              WHEN raw.cache_creation_tokens_5m + raw.cache_creation_tokens_1h > 0 THEN
                (raw.cache_creation_tokens_5m * raw.r_cache_create_5m) +
                (raw.cache_creation_tokens_1h * raw.r_cache_create_1h)
              ELSE
                raw.cache_creation_tokens * raw.r_cache_create
            END
          ) * raw.r_model * raw.r_group * sys.cost_factor
        ) AS cost_cache_write,
        IF(raw.r_price > 0,
          raw.r_price * raw.r_group * sys.cost_factor * sys.sys_quota_per_unit,
          0
        ) AS cost_fixed
      FROM raw
      CROSS JOIN sys
    )
    SELECT
      agg_date,
      COALESCE(token_name, '') AS token_name,
      COALESCE(model_name, '') AS model_name,
      COALESCE(username, '') AS username,
      COALESCE(`group`, '') AS group_name,
      COALESCE(channel_id, 0) AS channel_id,
      COALESCE(request_path, '[空路径]') AS request_path,
      COUNT(*) AS request_count,
      COALESCE(SUM(quota), 0) AS quota_total,
      COALESCE(SUM(cost_total), 0) AS actual_cost_total,
      COALESCE(SUM(pure_prompt_tokens), 0) AS input_tokens_total,
      COALESCE(SUM(cost_input), 0) AS input_cost_total,
      COALESCE(SUM(completion_tokens), 0) AS output_tokens_total,
      COALESCE(SUM(cost_output), 0) AS output_cost_total,
      COALESCE(SUM(cache_tokens), 0) AS cache_read_tokens_total,
      COALESCE(SUM(cost_cache_read), 0) AS cache_read_cost_total,
      COALESCE(SUM(cost_cache_saving), 0) AS cache_saving_total,
      COALESCE(SUM(cache_write_tokens_total), 0) AS cache_write_tokens_total,
      COALESCE(SUM(cost_cache_write), 0) AS cache_write_cost_total,
      COALESCE(SUM(cost_fixed), 0) AS fixed_cost_total
    FROM cost_detail
    GROUP BY agg_date, token_name, model_name, username, group_name, channel_id, request_path
    """

    settings = get_settings()
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            execute_query(
                cursor,
                delete_sql,
                delete_params,
                source_id=source.source_id,
                query_name="preagg_delete_range",
            )
            execute_query(
                cursor,
                insert_sql,
                params,
                source_id=source.source_id,
                query_name="preagg_refresh_insert",
            )
            conn.commit()

    return {
        "table": DAILY_AGG_TABLE,
        "source_id": source.source_id,
        "start_time": start_time,
        "end_time": end_time,
        "refreshed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def get_daily_aggregate_trend(
    source: SourceDefinition,
    filters: dict[str, Any],
    *,
    granularity: str,
) -> dict[str, Any]:
    where_parts = ["1=1"]
    params: list[Any] = []
    if filters.get("token_name"):
        where_parts.append("token_name = %s")
        params.append(filters["token_name"])
    if filters.get("model_name"):
        where_parts.append("model_name LIKE %s")
        params.append(f"%{filters['model_name']}%")
    if filters.get("username"):
        where_parts.append("username = %s")
        params.append(filters["username"])
    if filters.get("group_name"):
        where_parts.append("group_name = %s")
        params.append(filters["group_name"])
    if filters.get("channel_id"):
        where_parts.append("channel_id = %s")
        params.append(filters["channel_id"])
    if filters.get("request_id"):
        return {"granularity": granularity, "query_mode": "raw-fallback", "points": []}
    if filters.get("start_time"):
        where_parts.append("agg_date >= DATE(FROM_UNIXTIME(%s))")
        params.append(filters["start_time"])
    if filters.get("end_time"):
        where_parts.append("agg_date <= DATE(FROM_UNIXTIME(%s))")
        params.append(filters["end_time"])

    if granularity == "week":
        bucket_label = "CONCAT(YEAR(agg_date), '-W', LPAD(WEEK(agg_date, 3), 2, '0'))"
        bucket_sort = "MIN(UNIX_TIMESTAMP(agg_date))"
    else:
        bucket_label = "CAST(agg_date AS CHAR)"
        bucket_sort = "UNIX_TIMESTAMP(agg_date)"

    query = f"""
    SELECT
      {bucket_label} AS bucket_label,
      {bucket_sort} AS bucket_sort,
      SUM(request_count) AS request_count,
      SUM(quota_total) AS quota_total,
      SUM(actual_cost_total) AS actual_cost_total,
      SUM(input_cost_total) AS input_cost_total,
      SUM(output_cost_total) AS output_cost_total,
      SUM(cache_read_cost_total) AS cache_read_cost_total,
      SUM(cache_saving_total) AS cache_saving_total,
      SUM(cache_write_cost_total) AS cache_write_cost_total,
      SUM(fixed_cost_total) AS fixed_cost_total
    FROM {DAILY_AGG_TABLE}
    WHERE {' AND '.join(where_parts)}
    GROUP BY bucket_label
    ORDER BY bucket_sort ASC
    """
    settings = get_settings()
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            execute_query(
                cursor,
                query,
                params,
                source_id=source.source_id,
                query_name="preagg_trend",
            )
            points = cursor.fetchall() or []
    return {
        "granularity": granularity,
        "query_mode": "aggregate",
        "points": points,
    }
