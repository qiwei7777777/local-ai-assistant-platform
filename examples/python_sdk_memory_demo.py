from __future__ import annotations

import os

from local_ai_assistant_sdk import LocalAIAssistantClient


MEMORY_TEXT = "The user's preferred sign-off word is starlight."


def main() -> None:
    base_url = os.getenv("LOCAL_AI_ASSISTANT_BASE_URL", "http://127.0.0.1:8000")

    with LocalAIAssistantClient(base_url=base_url) as client:
        memory = client.create_memory(MEMORY_TEXT, source="sdk-demo")
        print("Created memory:", memory.id)

        memories = client.list_memories()
        print("Memory count:", len(memories.memories))

        chat = client.chat(
            message="According to my memory, what is my preferred sign-off word?",
            use_memory=True,
        )
        print("Assistant:", chat.assistant_message.content)

        deleted = client.delete_memory(memory.id)
        print("Deleted memory:", deleted.deleted)


if __name__ == "__main__":
    main()
