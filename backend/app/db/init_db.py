from pathlib import Path

from sqlalchemy import text

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models.chunk import Chunk
from app.models.file import FileRecord
from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_base_file import KnowledgeBaseFile
from app.models.memory import Memory
from app.models.message import Message
from app.models.session import ChatSession


def initialize_database() -> None:
    settings = get_settings()
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    db_file = settings.database_file_path
    if db_file is not None:
        db_file.parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)


def check_database() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
