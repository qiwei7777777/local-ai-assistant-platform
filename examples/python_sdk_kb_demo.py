from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path

from local_ai_assistant_sdk import LocalAIAssistantClient


SAMPLE_TEXT = """Nebula-42 is the internal codename for the local AI assistant demo project.
It is used in the knowledge base retrieval example.
"""


def build_sample_file() -> Path:
    temp_dir = Path(tempfile.gettempdir())
    sample_path = temp_dir / "local_ai_assistant_sdk_kb_demo.txt"
    sample_path.write_text(SAMPLE_TEXT, encoding="utf-8")
    return sample_path


def main() -> None:
    base_url = os.getenv("LOCAL_AI_ASSISTANT_BASE_URL", "http://127.0.0.1:8000")
    sample_file = build_sample_file()

    with LocalAIAssistantClient(base_url=base_url) as client:
        uploaded = client.upload_file(sample_file)
        print("Uploaded file:", uploaded.id, uploaded.original_name)

        kb_name = f"SDK KB Demo {datetime.now().strftime('%Y%m%d%H%M%S')}"
        knowledge_base = client.create_knowledge_base(
            name=kb_name,
            description="Knowledge base created by the Python SDK demo.",
        )
        print("Knowledge base:", knowledge_base.id, knowledge_base.name)

        attached = client.add_file_to_knowledge_base(knowledge_base.id, uploaded.id)
        print("Attached file:", attached.id)

        retrieval = client.search_knowledge_base(
            knowledge_base.id,
            "What is the internal codename?",
        )
        print("Retrieval hits:", len(retrieval.hits))
        if retrieval.hits:
            print("Top hit:", retrieval.hits[0].content)


if __name__ == "__main__":
    main()
