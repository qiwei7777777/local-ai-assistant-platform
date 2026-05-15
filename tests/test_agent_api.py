from __future__ import annotations

import sys
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

from app.api.deps import get_db, get_ollama_client, get_settings_dependency
from app.core.config import Settings
from app.db.base import Base
from app.main import app


class AgentFakeOllamaClient:
    """Fake that simulates a two-turn agent: tool call → final answer."""

    def __init__(self) -> None:
        self.call_count = 0

    def list_models(self) -> list[dict[str, object]]:
        return [{"name": "gemma4:e4b"}]

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
        tools: list[dict] | None = None,
    ) -> dict:
        self.call_count += 1

        if self.call_count == 1 and tools:
            # First turn: model decides to call list_directory on root
            return {
                "message": {
                    "role": "assistant",
                    "content": "Let me check the workspace structure first.",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "list_directory",
                                "arguments": {"path": "."},
                            }
                        }
                    ],
                }
            }

        # Second turn (or no tools): model returns final answer
        return {
            "message": {
                "role": "assistant",
                "content": "The workspace contains project files including a README and source code.",
            }
        }

    def chat_stream(self, **kwargs):
        raise NotImplementedError("Agent tests do not use streaming.")


class AlwaysToolFakeOllamaClient:
    """Fake that always returns a tool call — never a final answer. Used for max-iteration test."""

    def list_models(self) -> list[dict[str, object]]:
        return [{"name": "gemma4:e4b"}]

    def healthcheck(self) -> bool:
        return True

    def chat(self, **kwargs) -> dict:
        return {
            "message": {
                "role": "assistant",
                "content": "I need to check more.",
                "tool_calls": [
                    {
                        "function": {
                            "name": "list_directory",
                            "arguments": {"path": "."},
                        }
                    }
                ],
            }
        }

    def chat_stream(self, **kwargs):
        raise NotImplementedError


class UnknownToolFakeOllamaClient:
    """Fake that calls a tool not in the registry, then answers."""

    def __init__(self) -> None:
        self.call_count = 0

    def list_models(self) -> list[dict[str, object]]:
        return [{"name": "gemma4:e4b"}]

    def healthcheck(self) -> bool:
        return True

    def chat(self, **kwargs) -> dict:
        self.call_count += 1
        if self.call_count == 1:
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "nonexistent_tool",
                                "arguments": {"arg": "value"},
                            }
                        }
                    ],
                }
            }
        return {
            "message": {
                "role": "assistant",
                "content": "I tried a tool that does not exist, but I can still answer.",
            }
        }

    def chat_stream(self, **kwargs):
        raise NotImplementedError


class NeverToolFakeOllamaClient:
    """Fake where the model answers directly without calling any tools."""

    def list_models(self) -> list[dict[str, object]]:
        return [{"name": "gemma4:e4b"}]

    def healthcheck(self) -> bool:
        return True

    def chat(self, **kwargs) -> dict:
        return {
            "message": {
                "role": "assistant",
                "content": "I can answer without inspecting the workspace.",
            }
        }

    def chat_stream(self, **kwargs):
        raise NotImplementedError


class AgentApiTests(unittest.TestCase):
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
            CODE_WORKSPACE_ROOT="..",
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

        cls.fake_ollama = AgentFakeOllamaClient()

        def override_settings() -> Settings:
            return cls.settings

        def override_ollama_client() -> AgentFakeOllamaClient:
            return cls.fake_ollama

        def override_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_settings_dependency] = override_settings
        app.dependency_overrides[get_ollama_client] = override_ollama_client
        app.dependency_overrides[get_db] = override_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()
        app.dependency_overrides.clear()
        cls.engine.dispose()
        cls.temp_dir.cleanup()

    def setUp(self) -> None:
        self.fake_ollama.call_count = 0

    # ── Agent loop tests ─────────────────────────────
    def test_agent_chat_with_tool_call_loop(self) -> None:
        """Agent calls a tool on turn 1, gets result, responds on turn 2."""
        response = self.client.post(
            "/api/agent/chat",
            json={"message": "What is in this project?"},
        )
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload["success"], f"Expected success, got: {payload}")
        data = payload["data"]

        self.assertIn("workspace contains", data["content"].lower())
        self.assertEqual(data["model"], "gemma4:e4b")
        self.assertEqual(data["iterations"], 2)

        # Should have exactly one tool call record
        self.assertEqual(len(data["tool_calls_made"]), 1)
        tc = data["tool_calls_made"][0]
        self.assertEqual(tc["tool_name"], "list_directory")
        self.assertEqual(tc["arguments"], {"path": "."})
        self.assertIn("entries", tc["result_summary"])

        # Session + messages persisted
        self.assertIsNotNone(data["session_id"])
        self.assertIsNotNone(data["user_message_id"])
        self.assertIsNotNone(data["assistant_message_id"])

    def test_agent_chat_no_tools_needed(self) -> None:
        """Model answers directly without calling any tools."""
        # Swap in the NeverTool fake for this test
        original = self.fake_ollama
        never_tool = NeverToolFakeOllamaClient()

        def override_ollama_client() -> NeverToolFakeOllamaClient:
            return never_tool

        app.dependency_overrides[get_ollama_client] = override_ollama_client
        try:
            response = self.client.post(
                "/api/agent/chat",
                json={"message": "What is 2+2?"},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()["data"]
            self.assertEqual(data["iterations"], 1)
            self.assertEqual(len(data["tool_calls_made"]), 0)
            self.assertIn("I can answer", data["content"])
        finally:
            app.dependency_overrides[get_ollama_client] = (
                lambda: original
            )

    def test_agent_chat_session_continuation(self) -> None:
        """Verify that session_id is honored and a new message is added."""
        # Create first message
        resp1 = self.client.post(
            "/api/agent/chat",
            json={"message": "Hello agent."},
        )
        session_id = resp1.json()["data"]["session_id"]

        # Continue session
        resp2 = self.client.post(
            "/api/agent/chat",
            json={"message": "Continue please.", "session_id": session_id},
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["data"]["session_id"], session_id)

    def test_agent_max_iterations_exceeded(self) -> None:
        """Agent that keeps calling tools forever hits MAX_ITERATIONS and errors."""
        original = self.fake_ollama
        always_tool = AlwaysToolFakeOllamaClient()

        def override_ollama_client() -> AlwaysToolFakeOllamaClient:
            return always_tool

        app.dependency_overrides[get_ollama_client] = override_ollama_client
        try:
            response = self.client.post(
                "/api/agent/chat",
                json={"message": "Do something."},
            )
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json()["error"]["code"], "AGENT_MAX_ITERATIONS")
        finally:
            app.dependency_overrides[get_ollama_client] = lambda: original

    def test_agent_unknown_tool_fallback(self) -> None:
        """Model calls a tool not in the registry — the agent handles it gracefully."""
        original = self.fake_ollama
        unknown_tool = UnknownToolFakeOllamaClient()

        def override_ollama_client() -> UnknownToolFakeOllamaClient:
            return unknown_tool

        app.dependency_overrides[get_ollama_client] = override_ollama_client
        try:
            response = self.client.post(
                "/api/agent/chat",
                json={"message": "Try something."},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()["data"]
            self.assertEqual(len(data["tool_calls_made"]), 1)
            self.assertEqual(data["tool_calls_made"][0]["tool_name"], "nonexistent_tool")
            self.assertIn("Unknown tool", data["tool_calls_made"][0]["result_summary"])
        finally:
            app.dependency_overrides[get_ollama_client] = lambda: original

    def test_agent_chat_session_not_found(self) -> None:
        response = self.client.post(
            "/api/agent/chat",
            json={"message": "...", "session_id": "nonexistent-id"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "SESSION_NOT_FOUND")
