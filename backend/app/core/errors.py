from typing import Any


class AppError(Exception):
    """Application-level exception with an API-friendly error code."""

    def __init__(
        self,
        *,
        message: str,
        code: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
