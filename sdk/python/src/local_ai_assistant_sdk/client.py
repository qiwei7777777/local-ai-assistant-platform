from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

from local_ai_assistant_sdk.exceptions import (
    LocalAIAssistantAPIError,
    LocalAIAssistantConnectionError,
    LocalAIAssistantResponseError,
)
from local_ai_assistant_sdk.types import (
    APIResponse,
    ChatResult,
    DeleteResult,
    FileListResult,
    FileRecord,
    HealthStatus,
    KnowledgeBase,
    KnowledgeBaseFile,
    KnowledgeBaseFileListResult,
    KnowledgeBaseListResult,
    Memory,
    MemoryListResult,
    MessageListResult,
    ModelsResult,
    RetrievalResult,
    Session,
    SessionListResult,
)


class LocalAIAssistantClient:
    """Synchronous Python client for the Local AI Assistant backend."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        *,
        timeout: float = 120.0,
        headers: dict[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=headers or {},
        )

    def close(self) -> None:
        """Close the underlying HTTP client if it is owned by the SDK."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "LocalAIAssistantClient":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def health(self) -> HealthStatus:
        """Return backend health status."""
        return self._request("GET", "/api/health", model=HealthStatus)

    def healthcheck(self) -> HealthStatus:
        """Backward-compatible alias for :meth:`health`."""
        return self.health()

    def list_models(self) -> ModelsResult:
        """List local models exposed by the backend."""
        return self._request("GET", "/api/models", model=ModelsResult)

    def chat(
        self,
        *,
        message: str,
        session_id: str | None = None,
        knowledge_base_id: str | None = None,
        use_memory: bool = False,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatResult:
        """Send a chat request and return the assistant reply."""
        payload = {
            "message": message,
            "session_id": session_id,
            "knowledge_base_id": knowledge_base_id,
            "use_memory": use_memory,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        return self._request("POST", "/api/chat", json=payload, model=ChatResult)

    def create_session(self, title: str = "New Chat") -> Session:
        """Create an empty chat session."""
        return self._request(
            "POST",
            "/api/sessions",
            json={"title": title},
            model=Session,
        )

    def list_sessions(self) -> SessionListResult:
        """List persisted chat sessions ordered by latest activity."""
        return self._request("GET", "/api/sessions", model=SessionListResult)

    def get_session_messages(self, session_id: str) -> MessageListResult:
        """Fetch all messages for a specific session."""
        return self._request(
            "GET",
            f"/api/sessions/{session_id}/messages",
            model=MessageListResult,
        )

    def delete_session(self, session_id: str) -> DeleteResult:
        """Delete a chat session and its associated messages."""
        return self._request(
            "DELETE",
            f"/api/sessions/{session_id}",
            model=DeleteResult,
        )

    def upload_file(self, file_path: str | Path, *, content_type: str | None = None) -> FileRecord:
        """Upload and parse a local file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        guessed_content_type = content_type or self._guess_content_type(path.suffix.lower())
        with path.open("rb") as handle:
            files = {"file": (path.name, handle, guessed_content_type)}
            return self._request("POST", "/api/files/upload", files=files, model=FileRecord)

    def list_files(self) -> FileListResult:
        """List uploaded files with parse status."""
        return self._request("GET", "/api/files", model=FileListResult)

    def create_knowledge_base(self, name: str, description: str | None = None) -> KnowledgeBase:
        """Create a knowledge base."""
        return self._request(
            "POST",
            "/api/knowledge-bases",
            json={"name": name, "description": description},
            model=KnowledgeBase,
        )

    def list_knowledge_bases(self) -> KnowledgeBaseListResult:
        """List all knowledge bases."""
        return self._request("GET", "/api/knowledge-bases", model=KnowledgeBaseListResult)

    def add_file_to_knowledge_base(self, knowledge_base_id: str, file_id: str) -> KnowledgeBaseFile:
        """Attach a parsed file to a knowledge base and build chunks."""
        return self._request(
            "POST",
            f"/api/knowledge-bases/{knowledge_base_id}/files",
            json={"file_id": file_id},
            model=KnowledgeBaseFile,
        )

    def list_knowledge_base_files(self, knowledge_base_id: str) -> KnowledgeBaseFileListResult:
        """List files indexed in a knowledge base."""
        return self._request(
            "GET",
            f"/api/knowledge-bases/{knowledge_base_id}/files",
            model=KnowledgeBaseFileListResult,
        )

    def search_knowledge_base(
        self,
        knowledge_base_id: str,
        query: str,
        *,
        top_k: int | None = None,
    ) -> RetrievalResult:
        """Run a retrieval query against a knowledge base."""
        return self._request(
            "POST",
            "/api/retrieval/search",
            json={
                "knowledge_base_id": knowledge_base_id,
                "query": query,
                "top_k": top_k,
            },
            model=RetrievalResult,
        )

    def list_memories(self) -> MemoryListResult:
        """List explicit long-term memory items."""
        return self._request("GET", "/api/memories", model=MemoryListResult)

    def create_memory(self, content: str, *, source: str = "manual") -> Memory:
        """Create an explicit memory item."""
        return self._request(
            "POST",
            "/api/memories",
            json={"content": content, "source": source},
            model=Memory,
        )

    def delete_memory(self, memory_id: str) -> DeleteResult:
        """Delete a memory item."""
        return self._request(
            "DELETE",
            f"/api/memories/{memory_id}",
            model=DeleteResult,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        model: type[BaseModel] | None = None,
        **kwargs: Any,
    ) -> Any:
        headers = kwargs.pop("headers", {})
        if "json" in kwargs:
            headers = {"Content-Type": "application/json", **headers}

        try:
            response = self._client.request(method, path, headers=headers, **kwargs)
        except httpx.RequestError as exc:
            raise LocalAIAssistantConnectionError(
                "Unable to connect to the Local AI Assistant backend.",
                base_url=self.base_url,
                details={"reason": str(exc)},
            ) from exc

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise LocalAIAssistantResponseError(
                f"Backend returned a non-JSON response: {response.text[:200]}"
            ) from exc

        try:
            payload = APIResponse.model_validate(response_payload)
        except Exception as exc:  # noqa: BLE001
            raise LocalAIAssistantResponseError(
                f"Backend returned an invalid response shape: {response.text[:200]}"
            ) from exc

        if not response.is_success or not payload.success or payload.data is None:
            if payload.error is not None:
                raise LocalAIAssistantAPIError(
                    payload.error.message,
                    code=payload.error.code,
                    status_code=response.status_code,
                    details=payload.error.details,
                )
            raise LocalAIAssistantResponseError(
                f"Backend request failed with status {response.status_code}."
            )

        if model is None:
            return payload.data

        try:
            return model.model_validate(payload.data)
        except Exception as exc:  # noqa: BLE001
            raise LocalAIAssistantResponseError(
                f"Backend payload could not be parsed as {model.__name__}."
            ) from exc

    @staticmethod
    def _guess_content_type(suffix: str) -> str:
        mapping = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return mapping.get(suffix, "application/octet-stream")
