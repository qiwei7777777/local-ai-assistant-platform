from __future__ import annotations

import json
import time

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.integrations.ollama import OllamaClient
from app.repositories.message_repository import MessageRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.agent import AgentChatData, AgentChatRequest, AgentToolCallRecord
from app.services.agent_tools import AgentTools

AGENT_SYSTEM_PROMPT = (
    "You are a local coding agent with access to a workspace. "
    "You can list directories, read files, and search code to gather information. "
    "Use tools whenever you need to inspect the workspace before answering. "
    "Be thorough: check relevant files before drawing conclusions. "
    "When you have enough information from tools, answer concisely in the user's language."
)


class AgentService:
    MAX_ITERATIONS = 5

    def __init__(self, db: Session, settings: Settings, ollama_client: OllamaClient) -> None:
        self.db = db
        self.settings = settings
        self.ollama_client = ollama_client
        self.tools = AgentTools(settings)
        self.session_repo = SessionRepository(db)
        self.message_repo = MessageRepository(db)

    def run(self, request: AgentChatRequest) -> AgentChatData:
        session = self._get_or_create_session(request.session_id, request.message)

        user_msg = self.message_repo.create(
            session_id=session.id,
            role="user",
            content=request.message,
        )
        self.db.flush()

        selected_model = request.model or self.settings.ollama_default_model
        messages: list[dict] = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": request.message},
        ]
        tool_schemas = self._get_tool_schemas()
        tool_calls_made: list[AgentToolCallRecord] = []
        final_content = ""
        iterations = 0

        for i in range(self.MAX_ITERATIONS):
            iterations = i + 1
            response = self.ollama_client.chat(
                model=selected_model,
                messages=messages,
                tools=tool_schemas,
                temperature=request.temperature or 0.2,
                max_tokens=request.max_tokens or 2048,
                timeout=self.settings.code_agent_model_timeout,
            )

            msg = response.get("message", {})
            messages.append(msg)

            tool_calls = msg.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    func_name = tc["function"]["name"]
                    func_args = tc["function"]["arguments"]
                    if not isinstance(func_args, dict):
                        func_args = {}

                    result_text, duration_ms = self._execute_tool(func_name, func_args)
                    tool_calls_made.append(AgentToolCallRecord(
                        tool_name=func_name,
                        arguments=func_args,
                        result_summary=result_text[:500],
                        duration_ms=duration_ms,
                    ))
                    messages.append({
                        "role": "tool",
                        "content": result_text,
                        "name": func_name,
                    })
                continue

            final_content = msg.get("content", "").strip()
            if not final_content:
                raise AppError(
                    message="The model returned an empty response.",
                    code="AGENT_NO_RESPONSE",
                    status_code=502,
                )
            break
        else:
            raise AppError(
                message=f"Agent exceeded the maximum of {self.MAX_ITERATIONS} iterations without a final answer.",
                code="AGENT_MAX_ITERATIONS",
                status_code=500,
            )

        assistant_msg = self.message_repo.create(
            session_id=session.id,
            role="assistant",
            content=final_content,
        )
        self.session_repo.touch(session)
        self.db.commit()
        self.db.refresh(assistant_msg)

        return AgentChatData(
            session_id=session.id,
            user_message_id=user_msg.id,
            assistant_message_id=assistant_msg.id,
            model=selected_model,
            content=final_content,
            tool_calls_made=tool_calls_made,
            iterations=iterations,
        )

    # ── 私有方法 ──────────────────────────────────────
    def _get_or_create_session(self, session_id: str | None, message: str):
        if session_id:
            session = self.session_repo.get(session_id)
            if session is None:
                raise AppError(
                    message="Session not found.",
                    code="SESSION_NOT_FOUND",
                    status_code=404,
                )
            return session
        title = (message[:80] + "...") if len(message) > 80 else message
        return self.session_repo.create(title=title)

    def _get_tool_schemas(self) -> list[dict]:
        return self.tools.get_tool_schemas()

    def _execute_tool(self, name: str, arguments: dict) -> tuple[str, int]:
        start = time.perf_counter()
        try:
            result = self.tools.execute(name, arguments)
        except Exception as exc:
            result = json.dumps({"error": f"Tool execution failed: {exc}"}, ensure_ascii=False)

        duration_ms = int((time.perf_counter() - start) * 1000)
        return result, duration_ms
