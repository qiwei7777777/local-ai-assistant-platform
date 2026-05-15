from __future__ import annotations

import sys
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.api.deps import get_db, get_health_service, get_ollama_client, get_settings_dependency
from app.core.config import Settings
from app.db.base import Base
from app.main import app
from app.schemas.health import HealthStatus
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService


class FakeOllamaClient:
    def list_models(self) -> list[dict[str, object]]:
        return [{"name": "gemma4:e4b"}, {"name": "gemma4:26b"}]

    def healthcheck(self) -> bool:
        return True

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        timeout: int | None = None,
    ) -> dict[str, object]:
        all_content = "\n".join(message["content"] for message in messages)
        last_user_message = next(
            (message["content"] for message in reversed(messages) if message["role"] == "user"),
            "",
        ).lower()

        if "preferred sign-off word" in last_user_message and "starlight" in all_content.lower():
            answer = "Your preferred sign-off word is starlight."
        elif "codename" in last_user_message and "nebula-42" in all_content.lower():
            answer = "The project codename is Nebula-42."
        elif "return exactly this json shape" in last_user_message:
            answer = (
                '{"notes":"Created a tiny demo page.",'
                '"files":[{"path":"index.html","language":"html",'
                '"content":"<!doctype html><html><body><h1>Agent demo</h1></body></html>"}]}'
            )
        else:
            answer = f"This is a local AI assistant response from {model}."

        return {"message": {"content": answer}}

    def chat_stream(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        answer = self.chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )["message"]["content"]
        if answer == f"This is a local AI assistant response from {model}.":
            for chunk in ["This is ", "a local ", "AI assistant response ", f"from {model}."]:
                yield chunk
        else:
            yield answer


class FakeHealthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_status(self) -> HealthStatus:
        return HealthStatus(
            app="ok",
            version=self.settings.app_version,
            environment=self.settings.app_env,
            database="ok",
            ollama="ok",
            default_model=self.settings.ollama_default_model,
        )


class EmptyStreamOllamaClient(FakeOllamaClient):
    def chat_stream(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        if False:
            yield ""


class BackendApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(cls.temp_dir.name)
        cls.upload_dir = temp_path / "uploads"
        db_path = temp_path / "test.db"

        cls.settings = Settings(
            _env_file=None,
            APP_NAME="Local AI Assistant Platform",
            APP_VERSION="1.2.0",
            APP_ENV="test",
            APP_DEBUG=False,
            APP_HOST="0.0.0.0",
            APP_PORT=8000,
            DATABASE_URL=f"sqlite:///{db_path.as_posix()}",
            DATA_DIR=temp_path.as_posix(),
            UPLOAD_DIR=cls.upload_dir.as_posix(),
            OLLAMA_BASE_URL="http://fake-ollama.local",
            OLLAMA_DEFAULT_MODEL="gemma4:e4b",
            CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000",
        )

        cls.engine = create_engine(
            cls.settings.database_url,
            connect_args={"check_same_thread": False},
        )
        cls.SessionLocal = sessionmaker(
            bind=cls.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        Base.metadata.create_all(bind=cls.engine)

        def override_settings() -> Settings:
            return cls.settings

        def override_ollama_client() -> FakeOllamaClient:
            return FakeOllamaClient()

        def override_health_service() -> FakeHealthService:
            return FakeHealthService(cls.settings)

        def override_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_settings_dependency] = override_settings
        app.dependency_overrides[get_ollama_client] = override_ollama_client
        app.dependency_overrides[get_health_service] = override_health_service
        app.dependency_overrides[get_db] = override_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()
        app.dependency_overrides.clear()
        cls.engine.dispose()
        cls.temp_dir.cleanup()

    def test_health_and_models(self) -> None:
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        health_payload = health.json()
        self.assertTrue(health_payload["success"])
        self.assertEqual(health_payload["data"]["ollama"], "ok")
        self.assertEqual(health_payload["data"]["version"], "1.2.0")
        self.assertEqual(health_payload["data"]["environment"], "test")
        self.assertEqual(health_payload["data"]["default_model"], "gemma4:e4b")

        models = self.client.get("/api/models")
        self.assertEqual(models.status_code, 200)
        models_payload = models.json()["data"]
        self.assertEqual(models_payload["default_model"], "gemma4:e4b")
        self.assertIsInstance(models_payload["models"], list)
        self.assertTrue(all("name" in item for item in models_payload["models"]))
        model_names = [item["name"] for item in models_payload["models"]]
        self.assertIn("gemma4:e4b", model_names)
        self.assertIn("gemma4:26b", model_names)

    def test_chat_sessions_knowledge_base_and_memory_happy_path(self) -> None:
        memory_response = self.client.post(
            "/api/memories",
            json={
                "content": "The user prefers concise answers and their preferred sign-off word is starlight.",
                "source": "test-suite",
            },
        )
        self.assertEqual(memory_response.status_code, 201)
        memory_id = memory_response.json()["data"]["id"]

        session_response = self.client.post("/api/sessions", json={"title": "API Test Session"})
        self.assertEqual(session_response.status_code, 201)
        session_id = session_response.json()["data"]["id"]

        chat_response = self.client.post(
            "/api/chat",
            json={
                "session_id": session_id,
                "message": "According to my memory, what is my preferred sign-off word?",
                "use_memory": True,
                "model": "gemma4:26b",
            },
        )
        self.assertEqual(chat_response.status_code, 200)
        chat_data = chat_response.json()["data"]
        self.assertEqual(chat_data["session"]["id"], session_id)
        self.assertEqual(chat_data["model"], "gemma4:26b")
        self.assertGreaterEqual(chat_data["memory_hits_count"], 1)
        self.assertIn("starlight", chat_data["assistant_message"]["content"].lower())

        sessions_response = self.client.get("/api/sessions")
        self.assertEqual(sessions_response.status_code, 200)
        sessions = sessions_response.json()["data"]["sessions"]
        self.assertTrue(any(item["id"] == session_id for item in sessions))

        messages_response = self.client.get(f"/api/sessions/{session_id}/messages")
        self.assertEqual(messages_response.status_code, 200)
        messages = messages_response.json()["data"]["messages"]
        self.assertEqual(len(messages), 2)

        upload_response = self.client.post(
            "/api/files/upload",
            files={
                "file": (
                    "kb-demo.txt",
                    b"Nebula-42 is the internal codename for this project.",
                    "text/plain",
                )
            },
        )
        self.assertEqual(upload_response.status_code, 200)
        uploaded_file_id = upload_response.json()["data"]["id"]

        file_list_response = self.client.get("/api/files")
        self.assertEqual(file_list_response.status_code, 200)
        self.assertEqual(file_list_response.json()["data"]["files"][0]["status"], "parsed")

        kb_response = self.client.post(
            "/api/knowledge-bases",
            json={"name": "API Test KB", "description": "Knowledge base for API tests"},
        )
        self.assertEqual(kb_response.status_code, 201)
        knowledge_base_id = kb_response.json()["data"]["id"]

        attach_response = self.client.post(
            f"/api/knowledge-bases/{knowledge_base_id}/files",
            json={"file_id": uploaded_file_id},
        )
        self.assertEqual(attach_response.status_code, 200)

        kb_files_response = self.client.get(f"/api/knowledge-bases/{knowledge_base_id}/files")
        self.assertEqual(kb_files_response.status_code, 200)
        self.assertEqual(len(kb_files_response.json()["data"]["files"]), 1)

        retrieval_response = self.client.post(
            "/api/retrieval/search",
            json={"knowledge_base_id": knowledge_base_id, "query": "What is the codename?"},
        )
        self.assertEqual(retrieval_response.status_code, 200)
        hits = retrieval_response.json()["data"]["hits"]
        self.assertGreaterEqual(len(hits), 1)
        self.assertIn("Nebula-42", hits[0]["content"])

        kb_chat_response = self.client.post(
            "/api/chat",
            json={
                "message": "What is the project codename?",
                "knowledge_base_id": knowledge_base_id,
            },
        )
        self.assertEqual(kb_chat_response.status_code, 200)
        kb_chat_data = kb_chat_response.json()["data"]
        self.assertGreaterEqual(kb_chat_data["retrieval_hits_count"], 1)
        self.assertIn("Nebula-42", kb_chat_data["assistant_message"]["content"])

        delete_memory_response = self.client.delete(f"/api/memories/{memory_id}")
        self.assertEqual(delete_memory_response.status_code, 200)
        self.assertTrue(delete_memory_response.json()["data"]["deleted"])

        delete_session_response = self.client.delete(f"/api/sessions/{session_id}")
        self.assertEqual(delete_session_response.status_code, 200)
        self.assertTrue(delete_session_response.json()["data"]["deleted"])

    def test_chat_stream_persists_full_assistant_message(self) -> None:
        response = self.client.post(
            "/api/chat/stream",
            json={"message": "Say hello in streaming mode.", "model": "gemma4:e4b"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("event: chunk", response.text)
        self.assertIn("event: done", response.text)
        self.assertTrue(response.text.strip().endswith('"memory_hits_count": 0}'))

        sessions_response = self.client.get("/api/sessions")
        self.assertEqual(sessions_response.status_code, 200)
        session_id = sessions_response.json()["data"]["sessions"][0]["id"]

        messages_response = self.client.get(f"/api/sessions/{session_id}/messages")
        self.assertEqual(messages_response.status_code, 200)
        messages = messages_response.json()["data"]["messages"]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["content"], "This is a local AI assistant response from gemma4:e4b.")

    def test_aborted_stream_persists_partial_assistant_message(self) -> None:
        db = self.SessionLocal()
        try:
            service = ChatService(
                db=db,
                settings=self.settings,
                ollama_client=FakeOllamaClient(),  # type: ignore[arg-type]
            )
            stream = service.stream_chat_completion(
                ChatRequest(message="Write a long answer that can be interrupted.")
            )

            first_event = next(stream)
            self.assertIn("event: chunk", first_event)
            stream.close()
        finally:
            db.close()

        sessions_response = self.client.get("/api/sessions")
        self.assertEqual(sessions_response.status_code, 200)
        session_id = sessions_response.json()["data"]["sessions"][0]["id"]

        messages_response = self.client.get(f"/api/sessions/{session_id}/messages")
        self.assertEqual(messages_response.status_code, 200)
        messages = messages_response.json()["data"]["messages"]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["content"], "This is")

    def test_chat_rejects_unknown_model(self) -> None:
        response = self.client.post(
            "/api/chat",
            json={"message": "Hello", "model": "gemma4:missing"},
        )
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["code"], "MODEL_NOT_FOUND")

    def test_empty_stream_emits_error_event(self) -> None:
        db = self.SessionLocal()
        try:
            service = ChatService(
                db=db,
                settings=self.settings,
                ollama_client=EmptyStreamOllamaClient(),  # type: ignore[arg-type]
            )
            events = list(
                service.stream_chat_completion(
                    ChatRequest(message="Test an empty streaming response.")
                )
            )
        finally:
            db.close()

        self.assertEqual(len(events), 1)
        self.assertIn("event: error", events[0])
        self.assertIn("EMPTY_MODEL_RESPONSE", events[0])

    def test_code_agent_workspace_read_plan_and_command(self) -> None:
        workspace_response = self.client.get("/api/code-agent/workspace")
        self.assertEqual(workspace_response.status_code, 200)
        workspace_data = workspace_response.json()["data"]
        paths = [item["path"] for item in workspace_data["files"]]
        self.assertIn("README.md", paths)
        self.assertIn("git status --short", workspace_data["allowed_commands"])

        read_response = self.client.post("/api/code-agent/read", json={"path": "README.md"})
        self.assertEqual(read_response.status_code, 200)
        read_data = read_response.json()["data"]
        self.assertEqual(read_data["path"], "README.md")
        self.assertIn("Local AI Assistant Platform", read_data["content"])

        blocked_read = self.client.post("/api/code-agent/read", json={"path": "../outside.txt"})
        self.assertEqual(blocked_read.status_code, 400)
        self.assertEqual(blocked_read.json()["error"]["code"], "CODE_PATH_OUTSIDE_WORKSPACE")

        plan_response = self.client.post(
            "/api/code-agent/plan",
            json={
                "task": "Suggest one README improvement.",
                "file_paths": ["README.md"],
                "model": "gemma4:e4b",
            },
        )
        self.assertEqual(plan_response.status_code, 200)
        plan_data = plan_response.json()["data"]
        self.assertEqual(plan_data["model"], "gemma4:e4b")
        self.assertEqual(plan_data["context_files"][0]["path"], "README.md")
        self.assertTrue(plan_data["plan"])

        blocked_command = self.client.post("/api/code-agent/command", json={"command": "dir"})
        self.assertEqual(blocked_command.status_code, 400)
        self.assertEqual(blocked_command.json()["error"]["code"], "CODE_COMMAND_NOT_ALLOWED")

        command_response = self.client.post(
            "/api/code-agent/command",
            json={"command": "git status --short"},
        )
        self.assertEqual(command_response.status_code, 200)
        command_data = command_response.json()["data"]
        self.assertEqual(command_data["command"], "git status --short")
        self.assertIsInstance(command_data["exit_code"], int)

    def test_code_agent_generates_and_writes_files(self) -> None:
        output_dir = ROOT / "agent-output"
        try:
            generate_response = self.client.post(
                "/api/code-agent/generate",
                json={
                    "task": "Create a tiny static HTML page.",
                    "target_directory": "agent-output/test-page",
                    "file_paths": [],
                    "model": "gemma4:e4b",
                },
            )
            self.assertEqual(generate_response.status_code, 200)
            generated = generate_response.json()["data"]
            self.assertEqual(generated["target_directory"], "agent-output/test-page")
            self.assertEqual(generated["files"][0]["path"], "agent-output/test-page/index.html")
            self.assertIn("Agent demo", generated["files"][0]["content"])

            write_response = self.client.post(
                "/api/code-agent/write",
                json={"files": generated["files"], "overwrite": False},
            )
            self.assertEqual(write_response.status_code, 200)
            written = write_response.json()["data"]["written_files"]
            self.assertEqual(written[0]["path"], "agent-output/test-page/index.html")
            self.assertTrue((ROOT / "agent-output" / "test-page" / "index.html").exists())

            overwrite_blocked = self.client.post(
                "/api/code-agent/write",
                json={"files": generated["files"], "overwrite": False},
            )
            self.assertEqual(overwrite_blocked.status_code, 409)
            self.assertEqual(overwrite_blocked.json()["error"]["code"], "CODE_FILE_EXISTS")

            outside_write = self.client.post(
                "/api/code-agent/write",
                json={
                    "files": [
                        {
                            "path": "../outside.html",
                            "content": "<h1>Nope</h1>",
                            "language": "html",
                        }
                    ],
                    "overwrite": False,
                },
            )
            self.assertEqual(outside_write.status_code, 400)
            self.assertEqual(outside_write.json()["error"]["code"], "CODE_PATH_OUTSIDE_WORKSPACE")
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)


    def test_code_agent_file_too_large(self) -> None:
        large_dir = Path(self.temp_dir.name) / "large-test"
        large_dir.mkdir(exist_ok=True)
        large_file = large_dir / "big.txt"
        large_file.write_text("x" * 200_000, encoding="utf-8")

        large_settings = Settings(
            _env_file=None,
            CODE_WORKSPACE_ROOT=large_dir.as_posix(),
            CODE_AGENT_MAX_FILE_BYTES=120_000,
        )

        original_override = app.dependency_overrides.get(get_settings_dependency)
        app.dependency_overrides[get_settings_dependency] = lambda: large_settings
        try:
            read_resp = self.client.post("/api/code-agent/read", json={"path": "big.txt"})
            self.assertEqual(read_resp.status_code, 413)
            self.assertEqual(read_resp.json()["error"]["code"], "CODE_FILE_TOO_LARGE")
        finally:
            if original_override:
                app.dependency_overrides[get_settings_dependency] = original_override
            else:
                app.dependency_overrides.pop(get_settings_dependency, None)
            shutil.rmtree(large_dir, ignore_errors=True)

    def test_code_agent_workspace_not_found(self) -> None:
        missing_dir = Path(self.temp_dir.name) / "nonexistent-workspace"
        bad_settings = Settings(
            _env_file=None,
            CODE_WORKSPACE_ROOT=missing_dir.as_posix(),
        )

        original_override = app.dependency_overrides.get(get_settings_dependency)
        app.dependency_overrides[get_settings_dependency] = lambda: bad_settings
        try:
            resp = self.client.get("/api/code-agent/workspace")
            self.assertEqual(resp.status_code, 500)
            self.assertEqual(resp.json()["error"]["code"], "CODE_WORKSPACE_NOT_FOUND")
        finally:
            if original_override:
                app.dependency_overrides[get_settings_dependency] = original_override
            else:
                app.dependency_overrides.pop(get_settings_dependency, None)


if __name__ == "__main__":
    unittest.main()
