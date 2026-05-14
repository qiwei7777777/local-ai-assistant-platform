from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.models.chunk import Chunk
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_base_file import KnowledgeBaseFile


class KnowledgeBaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, name: str, description: str | None) -> KnowledgeBase:
        knowledge_base = KnowledgeBase(name=name, description=description)
        self.db.add(knowledge_base)
        self.db.flush()
        return knowledge_base

    def list_all(self) -> list[KnowledgeBase]:
        stmt = select(KnowledgeBase).order_by(KnowledgeBase.updated_at.desc())
        return list(self.db.scalars(stmt))

    def get(self, knowledge_base_id: str) -> KnowledgeBase | None:
        return self.db.get(KnowledgeBase, knowledge_base_id)

    def add_file(self, *, knowledge_base_id: str, file_id: str) -> KnowledgeBaseFile:
        link = KnowledgeBaseFile(knowledge_base_id=knowledge_base_id, file_id=file_id)
        self.db.add(link)
        self.db.flush()
        return link

    def get_link(self, *, knowledge_base_id: str, file_id: str) -> KnowledgeBaseFile | None:
        stmt = select(KnowledgeBaseFile).where(
            KnowledgeBaseFile.knowledge_base_id == knowledge_base_id,
            KnowledgeBaseFile.file_id == file_id,
        )
        return self.db.scalars(stmt).first()

    def list_files(self, knowledge_base_id: str) -> list[KnowledgeBaseFile]:
        stmt = (
            select(KnowledgeBaseFile)
            .where(KnowledgeBaseFile.knowledge_base_id == knowledge_base_id)
            .options(joinedload(KnowledgeBaseFile.file))
            .order_by(KnowledgeBaseFile.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def replace_chunks(
        self,
        *,
        knowledge_base_id: str,
        file_id: str,
        chunks: list[str],
    ) -> list[Chunk]:
        delete_stmt = delete(Chunk).where(
            Chunk.knowledge_base_id == knowledge_base_id,
            Chunk.file_id == file_id,
        )
        self.db.execute(delete_stmt)

        records: list[Chunk] = []
        for index, chunk in enumerate(chunks):
            record = Chunk(
                knowledge_base_id=knowledge_base_id,
                file_id=file_id,
                chunk_index=index,
                content=chunk,
            )
            self.db.add(record)
            records.append(record)
        self.db.flush()
        return records

    def list_chunks(self, knowledge_base_id: str) -> list[Chunk]:
        stmt = (
            select(Chunk)
            .where(Chunk.knowledge_base_id == knowledge_base_id)
            .options(joinedload(Chunk.file))
            .order_by(Chunk.file_id.asc(), Chunk.chunk_index.asc())
        )
        return list(self.db.scalars(stmt))

    def touch(self, knowledge_base: KnowledgeBase) -> KnowledgeBase:
        knowledge_base.updated_at = datetime.now(UTC)
        self.db.add(knowledge_base)
        self.db.flush()
        return knowledge_base
