from fastapi import UploadFile
from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.integrations.ollama import OllamaClient
from app.services.chat_service import ChatService
from app.services.file_service import FileService
from app.services.health_service import HealthService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.memory_service import MemoryService
from app.services.model_service import ModelService
from app.services.retrieval_service import RetrievalService
from app.services.session_service import SessionService


def get_settings_dependency() -> Settings:
    return get_settings()


def get_ollama_client(
    settings: Settings = Depends(get_settings_dependency),
) -> OllamaClient:
    return OllamaClient(settings)


def get_db(
    db: Session = Depends(get_db_session),
) -> Generator[Session, None, None]:
    yield db


def get_health_service(
    settings: Settings = Depends(get_settings_dependency),
    ollama_client: OllamaClient = Depends(get_ollama_client),
) -> HealthService:
    return HealthService(settings, ollama_client)


def get_model_service(
    settings: Settings = Depends(get_settings_dependency),
    ollama_client: OllamaClient = Depends(get_ollama_client),
) -> ModelService:
    return ModelService(settings, ollama_client)


def get_chat_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
    ollama_client: OllamaClient = Depends(get_ollama_client),
) -> ChatService:
    return ChatService(db, settings, ollama_client)


def get_session_service(
    db: Session = Depends(get_db),
) -> SessionService:
    return SessionService(db)


def get_file_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> FileService:
    return FileService(db, settings)


def get_knowledge_base_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> KnowledgeBaseService:
    return KnowledgeBaseService(db, settings)


def get_retrieval_service(
    settings: Settings = Depends(get_settings_dependency),
) -> RetrievalService:
    return RetrievalService(settings)


def get_memory_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> MemoryService:
    return MemoryService(db, settings)
