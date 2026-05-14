from __future__ import annotations

from typing import Any


class LocalAIAssistantSDKError(Exception):
    """Base exception for the Local AI Assistant Python SDK."""


class LocalAIAssistantConnectionError(LocalAIAssistantSDKError):
    """Raised when the SDK cannot connect to the backend service."""

    def __init__(self, message: str, *, base_url: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.base_url = base_url
        self.details = details or {}

    def __str__(self) -> str:
        return f"{super().__str__()} (base_url={self.base_url})"


class LocalAIAssistantAPIError(LocalAIAssistantSDKError):
    """Raised when the backend returns an application or HTTP error."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def __str__(self) -> str:
        return f"{super().__str__()} (code={self.code}, status_code={self.status_code})"


class LocalAIAssistantResponseError(LocalAIAssistantSDKError):
    """Raised when the backend returns a malformed or unsupported response."""
