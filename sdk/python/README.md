# Local AI Assistant Python SDK

Synchronous Python SDK for the Local AI Assistant FastAPI backend.

## Install

```powershell
cd D:\local_llm_test\sdk\python
python -m pip install -e .
```

## Quick Start

```python
from local_ai_assistant_sdk import LocalAIAssistantClient

with LocalAIAssistantClient("http://127.0.0.1:8000") as client:
    print(client.health())
    session = client.create_session("SDK Quickstart")
    result = client.chat(
        message="Please introduce yourself in one sentence.",
        session_id=session.id,
    )
    print(result.assistant_message.content)
```

## Covered APIs

- `health`
- `healthcheck`
- `list_models`
- `chat`
- `create_session`
- `list_sessions`
- `get_session_messages`
- `delete_session`
- `upload_file`
- `list_files`
- `create_knowledge_base`
- `list_knowledge_bases`
- `add_file_to_knowledge_base`
- `list_knowledge_base_files`
- `search_knowledge_base`
- `list_memories`
- `create_memory`
- `delete_memory`

## Exceptions

- `LocalAIAssistantConnectionError`: backend cannot be reached
- `LocalAIAssistantAPIError`: backend returned a structured API or HTTP error
- `LocalAIAssistantResponseError`: backend response could not be parsed by the SDK

## Examples

- `examples/python_sdk_quickstart.py`
- `examples/python_sdk_kb_demo.py`
- `examples/python_sdk_memory_demo.py`
