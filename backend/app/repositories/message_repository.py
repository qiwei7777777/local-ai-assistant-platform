from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, session_id: str, role: str, content: str) -> Message:
        message = Message(session_id=session_id, role=role, content=content)
        self.db.add(message)
        self.db.flush()
        return message

    def list_by_session(self, session_id: str) -> list[Message]:
        stmt = select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
        return list(self.db.scalars(stmt))
