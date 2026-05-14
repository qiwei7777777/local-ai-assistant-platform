from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.file import FileData


class KnowledgeBaseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class KnowledgeBaseAttachFileRequest(BaseModel):
    file_id: str


class KnowledgeBaseData(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseListData(BaseModel):
    knowledge_bases: list[KnowledgeBaseData]


class KnowledgeBaseFileData(BaseModel):
    id: str
    knowledge_base_id: str
    file_id: str
    created_at: datetime
    file: FileData


class KnowledgeBaseFileListData(BaseModel):
    knowledge_base_id: str
    files: list[KnowledgeBaseFileData]
