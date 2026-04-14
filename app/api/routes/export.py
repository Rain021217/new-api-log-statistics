import csv
from io import StringIO
from tempfile import NamedTemporaryFile

from openpyxl import Workbook
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.repositories.stats_repository import get_token_cost_export_rows
from app.services.audit_log import write_audit_event
from app.services.source_registry import get_source_registry

router = APIRouter()


def _require_source(source_id: str):
    registry = get_source_registry()
    source = registry.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Unknown source_id: {source_id}")
    return source


@router.get("/token-cost.csv")
def export_token_cost_csv(
    source_id: str = Query(...),
    token_name: str = Query(""),
    model_name: str = Query(""),
    username: str = Query(""),
    group_name: str = Query(""),
    ip: str = Query(""),
    channel_id: int | None = Query(None),
    request_id: str = Query(""),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
) -> Response:
    source = _require_source(source_id)
    filters = {
        "token_name": token_name.strip(),
        "model_name": model_name.strip(),
        "username": username.strip(),
        "group_name": group_name.strip(),
        "ip": ip.strip(),
        "channel_id": channel_id,
        "request_id": request_id.strip(),
        "start_time": start_time,
        "end_time": end_time,
    }
    rows = get_token_cost_export_rows(source, filters)
    write_audit_event(
        "export_token_cost_csv",
        {
            "source_id": source_id,
            "token_name": token_name,
            "model_name": model_name,
            "username": username,
            "group_name": group_name,
            "ip": ip,
            "channel_id": channel_id,
            "request_id": request_id,
            "start_time": start_time,
            "end_time": end_time,
            "row_count": len(rows),
        },
    )

    output = StringIO()
    writer = csv.writer(output)
    headers = [
        "请求ID",
        "调用时间",
        "用户名",
        "令牌名称",
        "模型名称",
        "渠道ID",
        "分组",
        "Request ID",
        "消耗总额度",
        "实际总花费",
        "常规输入Token",
        "常规输入单价",
        "常规输入花费",
        "输出Token",
        "输出单价",
        "输出花费",
        "缓存读取Token",
        "缓存读取单价",
        "缓存读取花费",
        "缓存创建Token",
        "缓存创建单价",
        "缓存创建花费",
        "按次固定花费",
    ]
    writer.writerow(headers)
    for row in rows:
        writer.writerow(
            [
                row["id"],
                row["created_at"],
                row["username"],
                row["token_name"],
                row["model_name"],
                row["channel_id"],
                row["group"],
                row["request_id"],
                row["quota"],
                row["cost_total"],
                row["pure_prompt_tokens"],
                row["up_input"],
                row["cost_input"],
                row["completion_tokens"],
                row["up_output"],
                row["cost_output"],
                row["cache_tokens"],
                row["up_cache_read"],
                row["cost_cache_read"],
                row["cache_write_tokens_total"],
                row["up_cache_write"],
                row["cost_cache_write"],
                row["cost_fixed"],
            ]
        )

    filename = "token-cost-export.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/token-cost.xlsx")
def export_token_cost_xlsx(
    source_id: str = Query(...),
    token_name: str = Query(""),
    model_name: str = Query(""),
    username: str = Query(""),
    group_name: str = Query(""),
    ip: str = Query(""),
    channel_id: int | None = Query(None),
    request_id: str = Query(""),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
) -> Response:
    source = _require_source(source_id)
    filters = {
        "token_name": token_name.strip(),
        "model_name": model_name.strip(),
        "username": username.strip(),
        "group_name": group_name.strip(),
        "ip": ip.strip(),
        "channel_id": channel_id,
        "request_id": request_id.strip(),
        "start_time": start_time,
        "end_time": end_time,
    }
    rows = get_token_cost_export_rows(source, filters)
    write_audit_event(
        "export_token_cost_xlsx",
        {
            "source_id": source_id,
            "token_name": token_name,
            "row_count": len(rows),
        },
    )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "token_cost"
    headers = [
        "请求ID",
        "调用时间",
        "用户名",
        "令牌名称",
        "模型名称",
        "渠道ID",
        "分组",
        "Request ID",
        "消耗总额度",
        "实际总花费",
        "常规输入Token",
        "常规输入单价",
        "常规输入花费",
        "输出Token",
        "输出单价",
        "输出花费",
        "缓存读取Token",
        "缓存读取单价",
        "缓存读取花费",
        "缓存创建Token",
        "缓存创建单价",
        "缓存创建花费",
        "按次固定花费",
    ]
    worksheet.append(headers)
    for row in rows:
        worksheet.append(
            [
                row["id"],
                row["created_at"],
                row["username"],
                row["token_name"],
                row["model_name"],
                row["channel_id"],
                row["group"],
                row["request_id"],
                row["quota"],
                row["cost_total"],
                row["pure_prompt_tokens"],
                row["up_input"],
                row["cost_input"],
                row["completion_tokens"],
                row["up_output"],
                row["cost_output"],
                row["cache_tokens"],
                row["up_cache_read"],
                row["cost_cache_read"],
                row["cache_write_tokens_total"],
                row["up_cache_write"],
                row["cost_cache_write"],
                row["cost_fixed"],
            ]
        )

    with NamedTemporaryFile(suffix=".xlsx") as temp_file:
        workbook.save(temp_file.name)
        temp_file.seek(0)
        content = temp_file.read()

    filename = "token-cost-export.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
