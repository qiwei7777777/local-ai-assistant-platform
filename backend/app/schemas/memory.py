from datetime import datetime

from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    source: str = Field(default="manual", min_length=1, max_length=64)


class MemoryData(BaseModel):
    id: str
    content: str
    source: str
    created_at: datetime
    metadata_json: str | None = None


class MemoryListData(BaseModel):
    memories: list[MemoryData]
