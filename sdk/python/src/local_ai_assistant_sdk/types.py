from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class APIErrorPayload(BaseModel):
    """Structured error payload returned by the backend."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class APIResponse(BaseModel):
    """Envelope used by all backend API responses."""

    success: bool
    data: Any | None = None
    error: APIErrorPayload | None = None


class DeleteResult(BaseModel):
    """Generic deletion response."""

    deleted: bool


class HealthStatus(BaseModel):
    app: str
    database: str
    ollama: str
    default_model: str


class ModelInfo(BaseModel):
    name: str
    size: int | None = None
    modified_at: str | None = None
    digest: str | None = None


class ModelsResult(BaseModel):
    default_model: str
    models: list[ModelInfo]


class Session(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class SessionListResult(BaseModel):
    sessions: list[Session]


class Message(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatMessage(BaseModel):
    """Message shape returned by the chat endpoint."""

    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class MessageListResult(BaseModel):
    session_id: str
    messages: list[Message]


class ChatResult(BaseModel):
    session: Session
    user_message: ChatMessage
    assistant_message: ChatMessage
    model: str
    knowledge_base_id: str | None = None
    retrieval_hits_count: int = 0
    used_memory: bool = False
    memory_hits_count: int = 0


class FileRecord(BaseModel):
    id: str
    original_name: str
    stored_path: str
    mime_type: str | None = None
    extension: str | None = None
    size: int
    status: str
    error_message: str | None = None
    extracted_text_length: int
    created_at: datetime
    updated_at: datetime


class FileListResult(BaseModel):
    files: list[FileRecord]


class KnowledgeBase(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseListResult(BaseModel):
    knowledge_bases: list[KnowledgeBase]


class KnowledgeBaseFile(BaseModel):
    id: str
    knowledge_base_id: str
    file_id: str
    created_at: datetime
    file: FileRecord


class KnowledgeBaseFileListResult(BaseModel):
    knowledge_base_id: str
    files: list[KnowledgeBaseFile]


class RetrievalHit(BaseModel):
    chunk_id: str
    file_id: str
    file_name: str
    chunk_index: int
    score: int
    content: str


class RetrievalResult(BaseModel):
    knowledge_base_id: str
    query: str
    hits: list[RetrievalHit]


class Memory(BaseModel):
    id: str
    content: str
    source: str
    created_at: datetime
    metadata_json: str | None = None


class MemoryListResult(BaseModel):
    memories: list[Memory]
