from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file import FileRecord


class FileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        original_name: str,
        stored_path: str,
        mime_type: str | None,
        extension: str | None,
        size: int,
    ) -> FileRecord:
        file = FileRecord(
            original_name=original_name,
            stored_path=stored_path,
            mime_type=mime_type,
            extension=extension,
            size=size,
            status="uploaded",
        )
        self.db.add(file)
        self.db.flush()
        return file

    def list_all(self) -> list[FileRecord]:
        stmt = select(FileRecord).order_by(FileRecord.created_at.desc())
        return list(self.db.scalars(stmt))

    def get(self, file_id: str) -> FileRecord | None:
        return self.db.get(FileRecord, file_id)

    def mark_processing(self, file: FileRecord) -> FileRecord:
        file.status = "processing"
        file.updated_at = datetime.now(UTC)
        self.db.add(file)
        self.db.flush()
        return file

    def mark_parsed(self, file: FileRecord, extracted_text: str) -> FileRecord:
        file.status = "parsed"
        file.error_message = None
        file.extracted_text = extracted_text
        file.extracted_text_length = len(extracted_text)
        file.updated_at = datetime.now(UTC)
        self.db.add(file)
        self.db.flush()
        return file

    def mark_failed(self, file: FileRecord, error_message: str) -> FileRecord:
        file.status = "failed"
        file.error_message = error_message
        file.updated_at = datetime.now(UTC)
        self.db.add(file)
        self.db.flush()
        return file
