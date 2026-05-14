from typing import Any

from pydantic import BaseModel, Field


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiResponse(BaseModel):
    success: bool
    data: Any | None = None
    error: ApiErrorDetail | None = None
