import json
from collections.abc import Iterator
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import AppError


class OllamaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.Client(
            base_url=settings.ollama_base_url,
            timeout=settings.ollama_request_timeout,
        )

    def list_models(self) -> list[dict[str, Any]]:
        try:
            response = self._client.get("/api/tags")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AppError(
                message="Failed to fetch Ollama models.",
                code="OLLAMA_UNAVAILABLE",
                status_code=503,
                details={"reason": str(exc)},
            ) from exc

        payload = response.json()
        return payload.get("models", [])

    def healthcheck(self) -> bool:
        self.list_models()
        return True

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = self._client.post("/api/chat", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AppError(
                message="Failed to call Ollama chat API.",
                code="OLLAMA_CHAT_FAILED",
                status_code=503,
                details={"reason": str(exc), "model": model},
            ) from exc

        return response.json()

    def chat_stream(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Iterator[str]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            with self._client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise AppError(
                            message="Received an invalid Ollama stream payload.",
                            code="OLLAMA_STREAM_INVALID",
                            status_code=502,
                            details={"line": line},
                        ) from exc

                    if chunk.get("done"):
                        break

                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
        except httpx.HTTPError as exc:
            raise AppError(
                message="Failed to call Ollama streaming chat API.",
                code="OLLAMA_STREAM_FAILED",
                status_code=503,
                details={"reason": str(exc), "model": model},
            ) from exc
