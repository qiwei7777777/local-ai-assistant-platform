import re

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.repositories.memory_repository import MemoryRepository
from app.schemas.memory import MemoryCreateRequest, MemoryData, MemoryListData


class MemoryService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.memory_repository = MemoryRepository(db)

    def list_memories(self) -> MemoryListData:
        return MemoryListData(
            memories=[self._to_memory_data(item) for item in self.memory_repository.list_all()]
        )

    def create_memory(self, payload: MemoryCreateRequest) -> MemoryData:
        record = self.memory_repository.create(
            content=payload.content.strip(),
            source=payload.source.strip() or "manual",
        )
        self.db.commit()
        self.db.refresh(record)
        return self._to_memory_data(record)

    def delete_memory(self, memory_id: str) -> None:
        deleted = self.memory_repository.delete(memory_id)
        if not deleted:
            self.db.rollback()
            raise AppError(
                message="Memory not found.",
                code="MEMORY_NOT_FOUND",
                status_code=404,
                details={"memory_id": memory_id},
            )
        self.db.commit()

    def find_relevant_memories(self, query: str) -> list[MemoryData]:
        tokens = self._tokenize_query(query)
        if not tokens:
            return []

        scored: list[tuple[int, object]] = []
        for memory in self.memory_repository.list_all():
            haystack = memory.content.lower()
            score = sum(haystack.count(token) for token in tokens)
            if score <= 0:
                continue
            scored.append((score, memory))

        scored.sort(key=lambda item: (-item[0], item[1].created_at), reverse=False)
        return [
            self._to_memory_data(item[1])
            for item in scored[: self.settings.memory_top_k]
        ]

    @staticmethod
    def _tokenize_query(query: str) -> list[str]:
        base_tokens = [token for token in re.findall(r"[\w\u4e00-\u9fff]+", query.lower()) if token]
        expanded: list[str] = []
        for token in base_tokens:
            expanded.append(token)
            if re.fullmatch(r"[\u4e00-\u9fff]+", token) and len(token) > 2:
                expanded.extend(token[index : index + 2] for index in range(len(token) - 1))
        return list(dict.fromkeys(expanded))

    @staticmethod
    def _to_memory_data(record) -> MemoryData:
        return MemoryData(
            id=record.id,
            content=record.content,
            source=record.source,
            created_at=record.created_at,
            metadata_json=record.metadata_json,
        )
