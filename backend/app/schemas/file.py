from datetime import datetime

from pydantic import BaseModel


class FileData(BaseModel):
    id: str
    original_name: str
    stored_path: str
    mime_type: str | None
    extension: str | None
    size: int
    status: str
    error_message: str | None
    extracted_text_length: int
    created_at: datetime
    updated_at: datetime


class FileListData(BaseModel):
    files: list[FileData]
