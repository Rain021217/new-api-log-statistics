from typing import Any

from app.core.config import get_settings
from app.db.source_client import execute_query, source_connection
from app.schemas.source import SourceDefinition
from app.services.preaggregation import get_daily_aggregate_trend, has_daily_aggregate_table


def _build_filtered_cost_cte(filters: dict[str, Any]) -> tuple[str, list[Any]]:
    where_parts = ["l.type = 2"]
    params: list[Any] = []

    if filters.get("token_name"):
        where_parts.append("l.token_name = %s")
        params.append(filters["token_name"])
    if filters.get("model_name"):
        where_parts.append("l.model_name LIKE %s")
        params.append(f"%{filters['model_name']}%")
    if filters.get("username"):
        where_parts.append("l.username = %s")
        params.append(filters["username"])
    if filters.get("group_name"):
        where_parts.append("l.`group` = %s")
        params.append(filters["group_name"])
    if filters.get("channel_id"):
        where_parts.append("l.channel_id = %s")
        params.append(filters["channel_id"])
    if filters.get("request_id"):
        where_parts.append("l.request_id = %s")
        params.append(filters["request_id"])
    if filters.get("ip"):
        where_parts.append("l.ip = %s")
        params.append(filters["ip"])
    if filters.get("start_time"):
        where_parts.append("l.created_at >= %s")
        params.append(filters["start_time"])
    if filters.get("end_time"):
        where_parts.append("l.created_at <= %s")
        params.append(filters["end_time"])

    where_sql = " AND ".join(where_parts)

    sql = f"""
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
        l.id,
        l.created_at,
        l.username,
        l.token_name,
        l.model_name,
        l.quota,
        l.prompt_tokens,
        l.completion_tokens,
        l.channel_id,
        l.`group`,
        l.request_id,
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
        raw.id,
        raw.created_at,
        raw.username,
        raw.token_name,
        raw.model_name,
        raw.quota,
        raw.prompt_tokens,
        raw.completion_tokens,
        raw.channel_id,
        raw.`group`,
        raw.request_id,
        raw.request_path,
        raw.cache_tokens,
        raw.cache_creation_tokens,
        raw.cache_creation_tokens_5m,
        raw.cache_creation_tokens_1h,
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
        ) AS cost_fixed,
        IF(raw.r_price > 0, 0,
          1000000 * raw.r_model * raw.r_group * sys.cost_factor
        ) AS up_input,
        IF(raw.r_price > 0, 0,
          1000000 * raw.r_model * raw.r_comp * raw.r_group * sys.cost_factor
        ) AS up_output,
        IF(raw.r_price > 0, 0,
          1000000 * raw.r_model * raw.r_cache * raw.r_group * sys.cost_factor
        ) AS up_cache_read
      FROM raw
      CROSS JOIN sys
    )
    """
    return sql, params


def _pick_granularity(filters: dict[str, Any], requested: str | None = None) -> str:
    if requested in {"hour", "day", "week"}:
        return requested
    start_time = filters.get("start_time")
    end_time = filters.get("end_time")
    if not start_time or not end_time or end_time <= start_time:
        return "day"
    span_seconds = end_time - start_time
    if span_seconds <= 2 * 24 * 3600:
        return "hour"
    if span_seconds <= 90 * 24 * 3600:
        return "day"
    return "week"


def _bucket_sql(granularity: str) -> tuple[str, str]:
    if granularity == "hour":
        label = (
            "CONCAT("
            "YEAR(FROM_UNIXTIME(created_at)), '-', "
            "LPAD(MONTH(FROM_UNIXTIME(created_at)), 2, '0'), '-', "
            "LPAD(DAY(FROM_UNIXTIME(created_at)), 2, '0'), ' ', "
            "LPAD(HOUR(FROM_UNIXTIME(created_at)), 2, '0'), ':00'"
            ")"
        )
        sort_value = (
            "UNIX_TIMESTAMP("
            "TIMESTAMP(DATE(FROM_UNIXTIME(created_at)), MAKETIME(HOUR(FROM_UNIXTIME(created_at)), 0, 0))"
            ")"
        )
    elif granularity == "week":
        label = "CONCAT(YEAR(FROM_UNIXTIME(created_at)), '-W', LPAD(WEEK(FROM_UNIXTIME(created_at), 3), 2, '0'))"
        sort_value = "MIN(created_at)"
    else:
        label = (
            "CONCAT("
            "YEAR(FROM_UNIXTIME(created_at)), '-', "
            "LPAD(MONTH(FROM_UNIXTIME(created_at)), 2, '0'), '-', "
            "LPAD(DAY(FROM_UNIXTIME(created_at)), 2, '0')"
            ")"
        )
        sort_value = "UNIX_TIMESTAMP(DATE(FROM_UNIXTIME(created_at)))"
    return label, sort_value


def _top_n_with_other(items: list[dict], *, key: str, top_n: int) -> list[dict]:
    ordered = sorted(items, key=lambda item: float(item.get(key) or 0), reverse=True)
    if len(ordered) <= top_n:
        return ordered
    head = ordered[:top_n]
    tail = ordered[top_n:]
    other = {
        "name": "其他",
        "request_count": sum(int(item.get("request_count") or 0) for item in tail),
        "actual_cost_total": sum(float(item.get("actual_cost_total") or 0) for item in tail),
        "quota_total": sum(float(item.get("quota_total") or 0) for item in tail),
    }
    head.append(other)
    return head


def get_token_cost_summary(source: SourceDefinition, filters: dict[str, Any]) -> dict:
    cte_sql, params = _build_filtered_cost_cte(filters)
    query = (
        cte_sql
        + """
    SELECT
      COUNT(*) AS request_count,
      COALESCE(SUM(quota), 0) AS quota_total,
      COALESCE(SUM(pure_prompt_tokens), 0) +
      COALESCE(SUM(completion_tokens), 0) +
      COALESCE(SUM(cache_tokens), 0) +
      COALESCE(SUM(cache_write_tokens_total), 0) AS total_tokens_consumed,
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
    """
    )
    settings = get_settings()
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            execute_query(
                cursor,
                query,
                params,
                source_id=source.source_id,
                query_name="token_cost_summary",
            )
            row = cursor.fetchone() or {}
    start_time = filters.get("start_time")
    end_time = filters.get("end_time")
    if start_time and end_time and end_time > start_time:
        minutes = max((end_time - start_time) / 60, 1)
        row["avg_rpm"] = float(row.get("request_count") or 0) / minutes
        row["avg_tpm"] = float(row.get("total_tokens_consumed") or 0) / minutes
    else:
        row["avg_rpm"] = 0
        row["avg_tpm"] = 0
    return row


def get_token_cost_details(
    source: SourceDefinition,
    filters: dict[str, Any],
    *,
    page: int = 1,
    page_size: int = 20,
    order_by: str = "created_at",
    order_dir: str = "desc",
) -> dict:
    cte_sql, params = _build_filtered_cost_cte(filters)
    safe_page = max(page, 1)
    safe_size = min(max(page_size, 1), 200)
    offset = (safe_page - 1) * safe_size
    allowed_order_fields = {
        "id": "id",
        "created_at": "created_at",
        "quota": "quota",
        "cost_total": "cost_total",
        "cost_input": "cost_input",
        "cost_output": "cost_output",
        "cost_cache_read": "cost_cache_read",
    }
    safe_order_by = allowed_order_fields.get(order_by, "created_at")
    safe_order_dir = "ASC" if order_dir.lower() == "asc" else "DESC"

    count_query = cte_sql + "SELECT COUNT(*) AS total FROM cost_detail"
    data_query = (
        cte_sql
        + """
    SELECT
      id,
      created_at,
      username,
      token_name,
      model_name,
      channel_id,
      `group`,
      request_id,
      quota,
      cost_total,
      pure_prompt_tokens,
      up_input,
      cost_input,
      completion_tokens,
      up_output,
      cost_output,
      cache_tokens,
      up_cache_read,
      cost_cache_read,
      cache_write_tokens_total,
      CASE
        WHEN cache_write_tokens_total > 0
        THEN (cost_cache_write * 1000000 / cache_write_tokens_total)
        ELSE 0
      END AS up_cache_write,
      cost_cache_write,
      cost_fixed
    FROM cost_detail
    ORDER BY """
        + f"{safe_order_by} {safe_order_dir}, id DESC "
        + """
    LIMIT %s OFFSET %s
    """
    )

    settings = get_settings()
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            execute_query(
                cursor,
                count_query,
                params,
                source_id=source.source_id,
                query_name="token_cost_details_count",
            )
            total = (cursor.fetchone() or {}).get("total", 0)
            execute_query(
                cursor,
                data_query,
                [*params, safe_size, offset],
                source_id=source.source_id,
                query_name="token_cost_details_rows",
            )
            items = cursor.fetchall() or []

    return {
        "items": items,
        "page": safe_page,
        "page_size": safe_size,
        "total": total,
    }


def get_token_cost_export_rows(
    source: SourceDefinition,
    filters: dict[str, Any],
) -> list[dict]:
    cte_sql, params = _build_filtered_cost_cte(filters)
    query = (
        cte_sql
        + """
    SELECT
      id,
      FROM_UNIXTIME(created_at) AS created_at,
      username,
      token_name,
      model_name,
      channel_id,
      `group`,
      request_id,
      quota,
      cost_total,
      pure_prompt_tokens,
      up_input,
      cost_input,
      completion_tokens,
      up_output,
      cost_output,
      cache_tokens,
      up_cache_read,
      cost_cache_read,
      cache_write_tokens_total,
      CASE
        WHEN cache_write_tokens_total > 0
        THEN (cost_cache_write * 1000000 / cache_write_tokens_total)
        ELSE 0
      END AS up_cache_write,
      cost_cache_write,
      cost_fixed
    FROM cost_detail
    ORDER BY created_at DESC, id DESC
    """
    )
    settings = get_settings()
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            execute_query(
                cursor,
                query,
                params,
                source_id=source.source_id,
                query_name="token_cost_export_rows",
            )
            return cursor.fetchall() or []


def get_token_cost_trend(
    source: SourceDefinition,
    filters: dict[str, Any],
    *,
    granularity: str | None = None,
) -> dict:
    actual_granularity = _pick_granularity(filters, requested=granularity)
    start_time = filters.get("start_time")
    end_time = filters.get("end_time")
    if (
        actual_granularity in {"day", "week"}
        and start_time
        and end_time
        and end_time > start_time
        and (end_time - start_time) >= 60 * 24 * 3600
        and has_daily_aggregate_table(source)
    ):
        return get_daily_aggregate_trend(
            source,
            filters,
            granularity=actual_granularity,
        )

    bucket_label_sql, bucket_sort_sql = _bucket_sql(actual_granularity)
    cte_sql, params = _build_filtered_cost_cte(filters)
    query = (
        cte_sql
        + f"""
    SELECT
      {bucket_label_sql} AS bucket_label,
      {bucket_sort_sql} AS bucket_sort,
      COUNT(*) AS request_count,
      COALESCE(SUM(quota), 0) AS quota_total,
      COALESCE(SUM(cost_total), 0) AS actual_cost_total,
      COALESCE(SUM(cost_input), 0) AS input_cost_total,
      COALESCE(SUM(cost_output), 0) AS output_cost_total,
      COALESCE(SUM(cost_cache_read), 0) AS cache_read_cost_total,
      COALESCE(SUM(cost_cache_saving), 0) AS cache_saving_total,
      COALESCE(SUM(cost_cache_write), 0) AS cache_write_cost_total,
      COALESCE(SUM(cost_fixed), 0) AS fixed_cost_total
    FROM cost_detail
    GROUP BY bucket_label
    ORDER BY bucket_sort ASC
    """
    )
    settings = get_settings()
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            execute_query(
                cursor,
                query,
                params,
                source_id=source.source_id,
                query_name="token_cost_trend",
            )
            points = cursor.fetchall() or []
    return {
        "granularity": actual_granularity,
        "query_mode": "raw",
        "points": points,
    }


def get_token_cost_breakdown(
    source: SourceDefinition,
    filters: dict[str, Any],
    *,
    top_n: int = 10,
) -> dict:
    cte_sql, params = _build_filtered_cost_cte(filters)
    dimensions = {
        "top_models": "COALESCE(NULLIF(model_name, ''), '[未知模型]')",
        "top_groups": "COALESCE(NULLIF(`group`, ''), '[空分组]')",
        "top_channels": "COALESCE(CAST(channel_id AS CHAR), '[空渠道]')",
        "top_request_paths": "COALESCE(NULLIF(request_path, ''), '[空路径]')",
    }
    settings = get_settings()
    result: dict[str, list[dict]] = {}
    with source_connection(source, connect_timeout=settings.request_timeout_seconds) as conn:
        with conn.cursor() as cursor:
            for output_key, expr in dimensions.items():
                query = (
                    cte_sql
                    + f"""
                SELECT
                  {expr} AS name,
                  COUNT(*) AS request_count,
                  COALESCE(SUM(quota), 0) AS quota_total,
                  COALESCE(SUM(cost_total), 0) AS actual_cost_total
                FROM cost_detail
                GROUP BY name
                ORDER BY actual_cost_total DESC, request_count DESC
                """
                )
                execute_query(
                    cursor,
                    query,
                    params,
                    source_id=source.source_id,
                    query_name=f"token_cost_breakdown:{output_key}",
                )
                rows = cursor.fetchall() or []
                result[output_key] = _top_n_with_other(rows, key="actual_cost_total", top_n=top_n)
    return result


def get_token_cost_charts(
    source: SourceDefinition,
    filters: dict[str, Any],
    *,
    granularity: str | None = None,
    top_n: int = 10,
) -> dict:
    trend = get_token_cost_trend(source, filters, granularity=granularity)
    breakdown = get_token_cost_breakdown(source, filters, top_n=top_n)
    model_cost_share = [
        {
            "category": item["name"],
            "value": item["actual_cost_total"],
            "request_count": item["request_count"],
        }
        for item in breakdown.get("top_models", [])
    ]
    return {
        "granularity": trend["granularity"],
        "query_mode": trend.get("query_mode", "raw"),
        "cost_trend": trend["points"],
        "request_trend": [
            {
                "bucket_label": point["bucket_label"],
                "bucket_sort": point["bucket_sort"],
                "request_count": point["request_count"],
            }
            for point in trend["points"]
        ],
        "stacked_cost_trend": trend["points"],
        "model_cost_share": model_cost_share,
        **breakdown,
    }
