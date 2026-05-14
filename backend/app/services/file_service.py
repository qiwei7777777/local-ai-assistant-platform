from pathlib import Path
from uuid import uuid4

from docx import Document
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.repositories.file_repository import FileRepository
from app.schemas.file import FileData, FileListData


class FileService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.file_repository = FileRepository(db)

    def list_files(self) -> FileListData:
        files = [self._to_file_data(item) for item in self.file_repository.list_all()]
        return FileListData(files=files)

    def get_file(self, file_id: str):
        file = self.file_repository.get(file_id)
        if file is None:
            raise AppError(
                message="File not found.",
                code="FILE_NOT_FOUND",
                status_code=404,
                details={"file_id": file_id},
            )
        return file

    def save_upload(self, *, filename: str, content_type: str | None, data: bytes) -> FileData:
        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        suffix = Path(filename).suffix.lower()
        stored_name = f"{uuid4().hex}{suffix}"
        stored_path = upload_dir / stored_name
        stored_path.write_bytes(data)

        file_record = self.file_repository.create(
            original_name=filename,
            stored_path=str(stored_path),
            mime_type=content_type,
            extension=suffix or None,
            size=len(data),
        )
        self.file_repository.mark_processing(file_record)
        self.db.commit()
        self.db.refresh(file_record)

        try:
            extracted_text = self._extract_text(stored_path, suffix)
            if not extracted_text.strip():
                raise AppError(
                    message="The file was parsed but produced no text content.",
                    code="EMPTY_FILE_CONTENT",
                    status_code=422,
                    details={"filename": filename},
                )
            self.file_repository.mark_parsed(file_record, extracted_text)
            self.db.commit()
            self.db.refresh(file_record)
        except Exception as exc:
            file_record = self.file_repository.get(file_record.id)
            if file_record is None:
                raise
            self.file_repository.mark_failed(file_record, str(exc))
            self.db.commit()
            self.db.refresh(file_record)
        return self._to_file_data(file_record)

    def _extract_text(self, path: Path, suffix: str) -> str:
        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if suffix == ".docx":
            document = Document(str(path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        raise AppError(
            message="Unsupported file type.",
            code="UNSUPPORTED_FILE_TYPE",
            status_code=415,
            details={"extension": suffix or "unknown"},
        )

    @staticmethod
    def _to_file_data(file_record) -> FileData:
        return FileData(
            id=file_record.id,
            original_name=file_record.original_name,
            stored_path=file_record.stored_path,
            mime_type=file_record.mime_type,
            extension=file_record.extension,
            size=file_record.size,
            status=file_record.status,
            error_message=file_record.error_message,
            extracted_text_length=file_record.extracted_text_length,
            created_at=file_record.created_at,
            updated_at=file_record.updated_at,
        )
