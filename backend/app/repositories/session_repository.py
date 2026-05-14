from sqlalchemy import select
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.session import ChatSession


class SessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, title: str) -> ChatSession:
        session = ChatSession(title=title)
        self.db.add(session)
        self.db.flush()
        return session

    def get(self, session_id: str) -> ChatSession | None:
        return self.db.get(ChatSession, session_id)

    def list_all(self) -> list[ChatSession]:
        stmt = select(ChatSession).order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        return list(self.db.scalars(stmt))

    def delete(self, session_id: str) -> bool:
        session = self.get(session_id)
        if session is None:
            return False
        self.db.delete(session)
        self.db.flush()
        return True

    def touch(self, session: ChatSession) -> ChatSession:
        session.updated_at = datetime.now(UTC)
        self.db.add(session)
        self.db.flush()
        return session

    def update_title(self, session: ChatSession, title: str) -> ChatSession:
        session.title = title
        session.updated_at = datetime.now(UTC)
        self.db.add(session)
        self.db.flush()
        return session
