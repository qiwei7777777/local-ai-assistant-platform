from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.memory import Memory


class MemoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, content: str, source: str, metadata_json: str | None = None) -> Memory:
        record = Memory(content=content, source=source, metadata_json=metadata_json)
        self.db.add(record)
        self.db.flush()
        return record

    def list_all(self) -> list[Memory]:
        stmt = select(Memory).order_by(Memory.created_at.desc())
        return list(self.db.scalars(stmt))

    def get(self, memory_id: str) -> Memory | None:
        return self.db.get(Memory, memory_id)

    def delete(self, memory_id: str) -> bool:
        stmt = delete(Memory).where(Memory.id == memory_id)
        result = self.db.execute(stmt)
        return result.rowcount > 0
