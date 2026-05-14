from __future__ import annotations

import json
import logging
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.integrations.ollama import OllamaClient
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.chat import ChatRequest, ChatResponseData, ChatMessageData, ChatSessionData
from app.services.memory_service import MemoryService
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, db: Session, settings: Settings, ollama_client: OllamaClient) -> None:
        self.db = db
        self.settings = settings
        self.ollama_client = ollama_client
        self.session_repository = SessionRepository(db)
        self.message_repository = MessageRepository(db)
        self.knowledge_base_repository = KnowledgeBaseRepository(db)
        self.memory_repository = MemoryRepository(db)
        self.retrieval_service = RetrievalService(settings)
        self.memory_service = MemoryService(db, settings)

    def create_chat_completion(self, payload: ChatRequest) -> ChatResponseData:
        try:
            prepared_chat = self._prepare_chat(payload)
            raw_response = self.ollama_client.chat(
                model=prepared_chat.selected_model,
                messages=prepared_chat.conversation,
                temperature=prepared_chat.temperature,
                max_tokens=prepared_chat.max_tokens,
            )
            assistant_content = raw_response.get("message", {}).get("content", "").strip()
            if not assistant_content:
                raise AppError(
                    message="Ollama returned an empty response.",
                    code="EMPTY_MODEL_RESPONSE",
                    status_code=502,
                )

            response_data = self._finalize_chat(prepared_chat, assistant_content)
        except Exception:
            self.db.rollback()
            raise

        return response_data

    def stream_chat_completion(self, payload: ChatRequest) -> Iterator[str]:
        prepared_chat: _PreparedChat | None = None
        assistant_chunks: list[str] = []

        try:
            prepared_chat = self._prepare_chat(payload)
            logger.info(
                "Starting chat stream with model=%s kb=%s use_memory=%s",
                prepared_chat.selected_model,
                bool(prepared_chat.payload.knowledge_base_id),
                prepared_chat.payload.use_memory,
            )

            for chunk in self.ollama_client.chat_stream(
                model=prepared_chat.selected_model,
                messages=prepared_chat.conversation,
                temperature=prepared_chat.temperature,
                max_tokens=prepared_chat.max_tokens,
            ):
                assistant_chunks.append(chunk)
                yield self._format_sse_event("chunk", {"content": chunk})

            assistant_content = "".join(assistant_chunks).strip()
            if not assistant_content:
                logger.warning(
                    "Chat stream completed with empty assistant content model=%s",
                    prepared_chat.selected_model,
                )
                raise AppError(
                    message="Ollama returned an empty response.",
                    code="EMPTY_MODEL_RESPONSE",
                    status_code=502,
                )

            response_data = self._finalize_chat(prepared_chat, assistant_content)
            logger.info(
                "Chat stream completed model=%s done=true chunks=%s",
                prepared_chat.selected_model,
                len(assistant_chunks),
            )
            yield self._format_sse_event("done", response_data.model_dump(mode="json"))
        except GeneratorExit:
            self._persist_partial_stream_response(prepared_chat, assistant_chunks)
            if prepared_chat is not None:
                logger.info(
                    "Chat stream aborted by client model=%s partial_chunks=%s",
                    prepared_chat.selected_model,
                    len(assistant_chunks),
                )
            raise
        except AppError as exc:
            self.db.rollback()
            yield self._format_sse_event(
                "error",
                {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            )
        except Exception as exc:
            self.db.rollback()
            yield self._format_sse_event(
                "error",
                {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred.",
                    "details": {"reason": str(exc)} if self.settings.app_debug else {},
                },
            )

    def _get_or_create_session(self, payload: ChatRequest):
        if payload.session_id:
            session = self.session_repository.get(payload.session_id)
            if session is None:
                raise AppError(
                    message="Session not found.",
                    code="SESSION_NOT_FOUND",
                    status_code=404,
                    details={"session_id": payload.session_id},
                )
            return session

        title = payload.message.strip().replace("\n", " ")[:60] or "New Chat"
        return self.session_repository.create(title=title)

    def _prepare_chat(self, payload: ChatRequest) -> "_PreparedChat":
        session = self._get_or_create_session(payload)
        existing_messages = self.message_repository.list_by_session(session.id)
        if not existing_messages and session.title == "New Chat":
            self.session_repository.update_title(
                session,
                payload.message.strip().replace("\n", " ")[:60] or "New Chat",
            )

        user_message = self.message_repository.create(
            session_id=session.id,
            role="user",
            content=payload.message,
        )

        conversation = [
            {"role": message.role, "content": message.content}
            for message in (existing_messages + [user_message])[-self.settings.chat_max_context_messages :]
        ]
        retrieval_hits_count = 0
        memory_hits_count = 0
        system_messages: list[dict[str, str]] = []

        if payload.use_memory:
            relevant_memories = self.memory_service.find_relevant_memories(payload.message)
            memory_hits_count = len(relevant_memories)
            if relevant_memories:
                memory_sections = []
                for item in relevant_memories:
                    memory_sections.append(f"[Memory | source={item.source}]\n{item.content}")
                memory_context = (
                    "Explicit user memory is provided below. Use it only when relevant to the user's question, "
                    "and keep the user's current request as the main task.\n\n"
                    f"User question:\n{payload.message}\n\n"
                    "Relevant memory:\n"
                    + "\n\n".join(memory_sections)
                )
                system_messages.append({"role": "system", "content": memory_context})

        if payload.knowledge_base_id:
            knowledge_base = self.knowledge_base_repository.get(payload.knowledge_base_id)
            if knowledge_base is None:
                raise AppError(
                    message="Knowledge base not found.",
                    code="KNOWLEDGE_BASE_NOT_FOUND",
                    status_code=404,
                    details={"knowledge_base_id": payload.knowledge_base_id},
                )
            chunks = self.knowledge_base_repository.list_chunks(payload.knowledge_base_id)
            retrieval = self.retrieval_service.search(
                knowledge_base_id=payload.knowledge_base_id,
                query=payload.message,
                chunks=chunks,
                top_k=self.settings.rag_top_k,
            )
            retrieval_hits_count = len(retrieval.hits)
            if retrieval.hits:
                context_sections = []
                for hit in retrieval.hits:
                    context_sections.append(
                        f"[Source: {hit.file_name} | Chunk {hit.chunk_index}]\n{hit.content}"
                    )
                context_message = (
                    "Knowledge base context is provided below. Use it only when relevant, "
                    "and keep the user's original question as the primary task.\n\n"
                    f"User question:\n{payload.message}\n\n"
                    "Retrieved context:\n"
                    + "\n\n".join(context_sections)
                )
                system_messages.append({"role": "system", "content": context_message})

        if system_messages:
            conversation = [*system_messages, *conversation]

        selected_model = self._resolve_selected_model(payload.model)

        return _PreparedChat(
            payload=payload,
            session=session,
            user_message=user_message,
            conversation=conversation,
            selected_model=selected_model,
            temperature=payload.temperature or self.settings.chat_default_temperature,
            max_tokens=payload.max_tokens or self.settings.chat_default_max_tokens,
            retrieval_hits_count=retrieval_hits_count,
            memory_hits_count=memory_hits_count,
        )

    def _finalize_chat(self, prepared_chat: "_PreparedChat", assistant_content: str) -> ChatResponseData:
        assistant_message = self.message_repository.create(
            session_id=prepared_chat.session.id,
            role="assistant",
            content=assistant_content,
        )
        self.session_repository.touch(prepared_chat.session)
        self.db.commit()
        self.db.refresh(prepared_chat.session)
        self.db.refresh(prepared_chat.user_message)
        self.db.refresh(assistant_message)

        return ChatResponseData(
            session=ChatSessionData(
                id=prepared_chat.session.id,
                title=prepared_chat.session.title,
                created_at=prepared_chat.session.created_at,
                updated_at=prepared_chat.session.updated_at,
            ),
            user_message=ChatMessageData(
                id=prepared_chat.user_message.id,
                role=prepared_chat.user_message.role,
                content=prepared_chat.user_message.content,
                created_at=prepared_chat.user_message.created_at,
            ),
            assistant_message=ChatMessageData(
                id=assistant_message.id,
                role=assistant_message.role,
                content=assistant_message.content,
                created_at=assistant_message.created_at,
            ),
            model=prepared_chat.selected_model,
            knowledge_base_id=prepared_chat.payload.knowledge_base_id,
            retrieval_hits_count=prepared_chat.retrieval_hits_count,
            used_memory=prepared_chat.payload.use_memory,
            memory_hits_count=prepared_chat.memory_hits_count,
        )

    def _persist_partial_stream_response(
        self,
        prepared_chat: "_PreparedChat" | None,
        assistant_chunks: list[str],
    ) -> None:
        if prepared_chat is None:
            self.db.rollback()
            return

        assistant_content = "".join(assistant_chunks).strip()
        if not assistant_content:
            self.db.rollback()
            return

        try:
            self._finalize_chat(prepared_chat, assistant_content)
        except Exception:
            self.db.rollback()

    def _resolve_selected_model(self, requested_model: str | None) -> str:
        if not requested_model:
            return self.settings.ollama_default_model

        available_models = {
            item.get("name")
            for item in self.ollama_client.list_models()
            if item.get("name")
        }
        if requested_model not in available_models:
            raise AppError(
                message="Requested model is not available in Ollama.",
                code="MODEL_NOT_FOUND",
                status_code=404,
                details={"model": requested_model},
            )

        return requested_model

    @staticmethod
    def _format_sse_event(event_type: str, payload: dict[str, object]) -> str:
        return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


class _PreparedChat:
    def __init__(
        self,
        *,
        payload: ChatRequest,
        session,
        user_message,
        conversation: list[dict[str, str]],
        selected_model: str,
        temperature: float,
        max_tokens: int,
        retrieval_hits_count: int,
        memory_hits_count: int,
    ) -> None:
        self.payload = payload
        self.session = session
        self.user_message = user_message
        self.conversation = conversation
        self.selected_model = selected_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.retrieval_hits_count = retrieval_hits_count
        self.memory_hits_count = memory_hits_count
