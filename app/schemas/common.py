from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    ok: bool = True
    data: Any = None
    message: str = ""
    error: dict[str, Any] | None = None


def success_response(data: Any = None, message: str = "") -> dict[str, Any]:
    return ApiResponse(ok=True, data=data, message=message).model_dump(mode="json")


def error_response(
    message: str,
    *,
    error_type: str = "Error",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "type": error_type,
        **(extra or {}),
    }
    return ApiResponse(
        ok=False,
        message=message,
        error=payload,
    ).model_dump(mode="json")
