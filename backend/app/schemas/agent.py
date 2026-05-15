from __future__ import annotations

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)


class AgentToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict
    result_summary: str
    duration_ms: int


class AgentChatData(BaseModel):
    session_id: str
    user_message_id: str
    assistant_message_id: str
    model: str
    content: str
    tool_calls_made: list[AgentToolCallRecord]
    iterations: int
