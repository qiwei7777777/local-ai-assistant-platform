# Python SDK

The Python SDK wraps the FastAPI backend for scripts, notebooks, and automation demos.

## Install

```powershell
cd D:\local_llm_test\sdk\python
python -m pip install -e .
```

## Quick Example

```python
from local_ai_assistant_sdk import LocalAIAssistantClient

client = LocalAIAssistantClient(base_url="http://127.0.0.1:8000")
result = client.chat(message="Summarize the project in one paragraph.")
print(result.assistant_message.content)
client.close()
```

## Examples

- `examples/python_sdk_quickstart.py`
- `examples/python_sdk_kb_demo.py`
- `examples/python_sdk_memory_demo.py`

## Design

The SDK returns typed objects and wraps backend API failures in clear Python exceptions. It is intentionally thin so the backend remains the source of truth.
