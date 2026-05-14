from datetime import datetime

from pydantic import BaseModel


class MessageData(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime


class MessageListData(BaseModel):
    session_id: str
    messages: list[MessageData]
