from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.repositories.file_repository import FileRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.file import FileData
from app.schemas.knowledge_base import (
    KnowledgeBaseAttachFileRequest,
    KnowledgeBaseCreateRequest,
    KnowledgeBaseData,
    KnowledgeBaseFileData,
    KnowledgeBaseFileListData,
    KnowledgeBaseListData,
)
from app.services.file_service import FileService
from app.services.retrieval_service import RetrievalService


class KnowledgeBaseService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.knowledge_base_repository = KnowledgeBaseRepository(db)
        self.file_repository = FileRepository(db)
        self.retrieval_service = RetrievalService(settings)

    def list_knowledge_bases(self) -> KnowledgeBaseListData:
        items = [
            self._to_knowledge_base_data(item)
            for item in self.knowledge_base_repository.list_all()
        ]
        return KnowledgeBaseListData(knowledge_bases=items)

    def create_knowledge_base(self, payload: KnowledgeBaseCreateRequest) -> KnowledgeBaseData:
        try:
            record = self.knowledge_base_repository.create(
                name=payload.name.strip(),
                description=payload.description.strip() if payload.description else None,
            )
            self.db.commit()
            self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError(
                message="Knowledge base name already exists.",
                code="KNOWLEDGE_BASE_EXISTS",
                status_code=409,
                details={"name": payload.name},
            ) from exc
        return self._to_knowledge_base_data(record)

    def attach_file(
        self,
        knowledge_base_id: str,
        payload: KnowledgeBaseAttachFileRequest,
    ) -> KnowledgeBaseFileData:
        knowledge_base = self.knowledge_base_repository.get(knowledge_base_id)
        if knowledge_base is None:
            raise AppError(
                message="Knowledge base not found.",
                code="KNOWLEDGE_BASE_NOT_FOUND",
                status_code=404,
                details={"knowledge_base_id": knowledge_base_id},
            )

        file_record = self.file_repository.get(payload.file_id)
        if file_record is None:
            raise AppError(
                message="File not found.",
                code="FILE_NOT_FOUND",
                status_code=404,
                details={"file_id": payload.file_id},
            )
        if file_record.status != "parsed" or not file_record.extracted_text:
            raise AppError(
                message="Only successfully parsed files can be added to a knowledge base.",
                code="FILE_NOT_READY",
                status_code=422,
                details={"file_id": payload.file_id, "status": file_record.status},
            )

        existing_link = self.knowledge_base_repository.get_link(
            knowledge_base_id=knowledge_base_id,
            file_id=payload.file_id,
        )
        if existing_link is None:
            link = self.knowledge_base_repository.add_file(
                knowledge_base_id=knowledge_base_id,
                file_id=payload.file_id,
            )
        else:
            link = existing_link

        chunks = self.retrieval_service.split_text(file_record.extracted_text)
        self.knowledge_base_repository.replace_chunks(
            knowledge_base_id=knowledge_base_id,
            file_id=payload.file_id,
            chunks=chunks,
        )
        self.knowledge_base_repository.touch(knowledge_base)
        self.db.commit()
        self.db.refresh(link)
        self.db.refresh(file_record)
        return KnowledgeBaseFileData(
            id=link.id,
            knowledge_base_id=link.knowledge_base_id,
            file_id=link.file_id,
            created_at=link.created_at,
            file=FileService._to_file_data(file_record),
        )

    def list_files(self, knowledge_base_id: str) -> KnowledgeBaseFileListData:
        knowledge_base = self.knowledge_base_repository.get(knowledge_base_id)
        if knowledge_base is None:
            raise AppError(
                message="Knowledge base not found.",
                code="KNOWLEDGE_BASE_NOT_FOUND",
                status_code=404,
                details={"knowledge_base_id": knowledge_base_id},
            )
        links = self.knowledge_base_repository.list_files(knowledge_base_id)
        return KnowledgeBaseFileListData(
            knowledge_base_id=knowledge_base_id,
            files=[
                KnowledgeBaseFileData(
                    id=link.id,
                    knowledge_base_id=link.knowledge_base_id,
                    file_id=link.file_id,
                    created_at=link.created_at,
                    file=FileService._to_file_data(link.file),
                )
                for link in links
            ],
        )

    def get_knowledge_base_or_error(self, knowledge_base_id: str):
        knowledge_base = self.knowledge_base_repository.get(knowledge_base_id)
        if knowledge_base is None:
            raise AppError(
                message="Knowledge base not found.",
                code="KNOWLEDGE_BASE_NOT_FOUND",
                status_code=404,
                details={"knowledge_base_id": knowledge_base_id},
            )
        return knowledge_base

    @staticmethod
    def _to_knowledge_base_data(record) -> KnowledgeBaseData:
        return KnowledgeBaseData(
            id=record.id,
            name=record.name,
            description=record.description,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
