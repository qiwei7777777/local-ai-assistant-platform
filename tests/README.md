# Tests

## Coverage

- `test_backend_api.py`
  - Health and model endpoints
  - Chat, sessions, files, knowledge bases, retrieval, and memory happy path
  - Streaming persistence
  - Partial stream persistence after abort
  - Empty stream error handling
  - Unknown model rejection
- `test_sdk_client.py`
  - SDK response parsing
  - SDK API error wrapping
  - SDK connection error wrapping

## Run

```powershell
cd D:\local_llm_test\backend
python -m pip install -e ".[dev]"

cd D:\local_llm_test
python -m unittest discover -s tests -p "test_*.py"
```

The backend API tests use a temporary SQLite database and fake Ollama client, so they do not require a real local model.
