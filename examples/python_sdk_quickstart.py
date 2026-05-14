from __future__ import annotations

import os

from local_ai_assistant_sdk import LocalAIAssistantClient


def main() -> None:
    base_url = os.getenv("LOCAL_AI_ASSISTANT_BASE_URL", "http://127.0.0.1:8000")

    with LocalAIAssistantClient(base_url=base_url) as client:
        health = client.health()
        print("Health:", health.model_dump())

        models = client.list_models()
        print("Models:", [model.name for model in models.models])

        session = client.create_session("SDK Quickstart Demo")
        print("Session created:", session.id)

        result = client.chat(
            session_id=session.id,
            message="Please reply with one short sentence about this local AI assistant.",
        )
        print("Assistant:", result.assistant_message.content)

        messages = client.get_session_messages(session.id)
        print("Message count:", len(messages.messages))


if __name__ == "__main__":
    main()
