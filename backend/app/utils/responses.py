from typing import Any

from app.schemas.common import ApiErrorDetail


def success_response(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data, "error": None}


def error_response(*, code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    error = ApiErrorDetail(code=code, message=message, details=details or {})
    return {"success": False, "data": None, "error": error.model_dump()}
