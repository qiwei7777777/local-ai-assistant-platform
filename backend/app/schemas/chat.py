from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, description="Existing session ID; omitted to create a new session.")
    message: str = Field(min_length=1, description="User message content.")
    knowledge_base_id: str | None = Field(default=None, description="Optional knowledge base for retrieval augmentation.")
    use_memory: bool = Field(default=False, description="Whether to inject explicit long-term memory.")
    model: str | None = Field(default=None, description="Optional Ollama model name.")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)


class ChatMessageData(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class ChatSessionData(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatResponseData(BaseModel):
    session: ChatSessionData
    user_message: ChatMessageData
    assistant_message: ChatMessageData
    model: str
    knowledge_base_id: str | None = None
    retrieval_hits_count: int = 0
    used_memory: bool = False
    memory_hits_count: int = 0


class ChatStreamEvent(BaseModel):
    type: str
    content: str | None = None
    data: ChatResponseData | None = None
    error: dict[str, object] | None = None
