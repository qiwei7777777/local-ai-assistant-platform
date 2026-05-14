from __future__ import annotations

import sys
import unittest
from pathlib import Path

import httpx

SDK_SRC = Path(__file__).resolve().parents[1] / "sdk" / "python" / "src"
if str(SDK_SRC) not in sys.path:
    sys.path.insert(0, str(SDK_SRC))

from local_ai_assistant_sdk import (
    LocalAIAssistantAPIError,
    LocalAIAssistantClient,
    LocalAIAssistantConnectionError,
)


def build_transport(handler):
    return httpx.MockTransport(handler)


class LocalAIAssistantClientTests(unittest.TestCase):
    def test_chat_parses_chat_message_without_session_id(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api/chat")
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "session": {
                            "id": "session-1",
                            "title": "Demo",
                            "created_at": "2026-04-09T12:00:00",
                            "updated_at": "2026-04-09T12:00:00",
                        },
                        "user_message": {
                            "id": "message-1",
                            "role": "user",
                            "content": "hello",
                            "created_at": "2026-04-09T12:00:00",
                        },
                        "assistant_message": {
                            "id": "message-2",
                            "role": "assistant",
                            "content": "hi",
                            "created_at": "2026-04-09T12:00:01",
                        },
                        "model": "gemma4:e4b",
                        "knowledge_base_id": None,
                        "retrieval_hits_count": 0,
                        "used_memory": False,
                        "memory_hits_count": 0,
                    },
                    "error": None,
                },
            )

        http_client = httpx.Client(
            base_url="http://testserver",
            transport=build_transport(handler),
        )
        client = LocalAIAssistantClient(base_url="http://testserver", http_client=http_client)

        result = client.chat(message="hello")

        self.assertEqual(result.assistant_message.content, "hi")
        self.assertEqual(result.user_message.role, "user")
        client.close()
        http_client.close()

    def test_api_error_is_wrapped(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                404,
                json={
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "MEMORY_NOT_FOUND",
                        "message": "Memory not found.",
                        "details": {"memory_id": "missing"},
                    },
                },
            )

        http_client = httpx.Client(
            base_url="http://testserver",
            transport=build_transport(handler),
        )
        client = LocalAIAssistantClient(base_url="http://testserver", http_client=http_client)

        with self.assertRaises(LocalAIAssistantAPIError) as ctx:
            client.delete_memory("missing")

        self.assertEqual(ctx.exception.code, "MEMORY_NOT_FOUND")
        self.assertEqual(ctx.exception.status_code, 404)
        client.close()
        http_client.close()

    def test_connection_error_is_wrapped(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("boom", request=request)

        http_client = httpx.Client(
            base_url="http://testserver",
            transport=build_transport(handler),
        )
        client = LocalAIAssistantClient(base_url="http://testserver", http_client=http_client)

        with self.assertRaises(LocalAIAssistantConnectionError):
            client.list_models()

        client.close()
        http_client.close()


if __name__ == "__main__":
    unittest.main()
