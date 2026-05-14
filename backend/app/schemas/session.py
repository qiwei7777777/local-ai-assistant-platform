from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    title: str = Field(default="New Chat", min_length=1, max_length=255)


class SessionUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class SessionData(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class SessionListData(BaseModel):
    sessions: list[SessionData]
