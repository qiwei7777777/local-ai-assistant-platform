from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.repositories.message_repository import MessageRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.message import MessageData, MessageListData
from app.schemas.session import SessionCreateRequest, SessionData, SessionListData, SessionUpdateRequest


class SessionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.session_repository = SessionRepository(db)
        self.message_repository = MessageRepository(db)

    def list_sessions(self) -> SessionListData:
        sessions = [self._to_session_data(item) for item in self.session_repository.list_all()]
        return SessionListData(sessions=sessions)

    def create_session(self, payload: SessionCreateRequest) -> SessionData:
        session = self.session_repository.create(title=payload.title.strip() or "New Chat")
        self.db.commit()
        self.db.refresh(session)
        return self._to_session_data(session)

    def update_session(self, session_id: str, payload: SessionUpdateRequest) -> SessionData:
        session = self.session_repository.get(session_id)
        if session is None:
            raise AppError(
                message="Session not found.",
                code="SESSION_NOT_FOUND",
                status_code=404,
                details={"session_id": session_id},
            )
        session = self.session_repository.update_title(session, payload.title.strip())
        self.db.commit()
        self.db.refresh(session)
        return self._to_session_data(session)

    def delete_session(self, session_id: str) -> None:
        deleted = self.session_repository.delete(session_id)
        if not deleted:
            self.db.rollback()
            raise AppError(
                message="Session not found.",
                code="SESSION_NOT_FOUND",
                status_code=404,
                details={"session_id": session_id},
            )
        self.db.commit()

    def list_messages(self, session_id: str) -> MessageListData:
        session = self.session_repository.get(session_id)
        if session is None:
            raise AppError(
                message="Session not found.",
                code="SESSION_NOT_FOUND",
                status_code=404,
                details={"session_id": session_id},
            )

        messages = [
            MessageData(
                id=item.id,
                session_id=item.session_id,
                role=item.role,
                content=item.content,
                created_at=item.created_at,
            )
            for item in self.message_repository.list_by_session(session_id)
        ]
        return MessageListData(session_id=session_id, messages=messages)

    @staticmethod
    def _to_session_data(session) -> SessionData:
        return SessionData(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
