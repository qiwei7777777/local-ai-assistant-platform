# Backend

The backend is a FastAPI service that exposes chat, session, file, knowledge-base, retrieval, memory, model, and health APIs.

## Structure

```text
backend/app/api/             FastAPI routers and dependencies
backend/app/core/            settings and shared errors
backend/app/db/              SQLAlchemy engine/session/bootstrap
backend/app/integrations/    Ollama client
backend/app/models/          SQLAlchemy models
backend/app/repositories/    persistence access layer
backend/app/schemas/         Pydantic request/response models
backend/app/services/        business workflows
backend/app/utils/           response helpers
```

## Runtime

```powershell
cd D:\local_llm_test\backend
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend reads root `.env` and `backend/.env`-style settings through Pydantic Settings.

## Key Environment Variables

- `APP_NAME`
- `APP_VERSION`
- `APP_ENV`
- `APP_DEBUG`
- `APP_HOST`
- `APP_PORT`
- `CORS_ORIGINS`
- `CORS_ORIGIN_REGEX`
- `DATABASE_URL`
- `DATA_DIR`
- `UPLOAD_DIR`
- `VECTOR_STORE_DIR`
- `OLLAMA_BASE_URL`
- `OLLAMA_DEFAULT_MODEL`
- `OLLAMA_REQUEST_TIMEOUT`
- `CHAT_DEFAULT_TEMPERATURE`
- `CHAT_DEFAULT_MAX_TOKENS`
- `CHAT_MAX_CONTEXT_MESSAGES`
- `RAG_CHUNK_SIZE`
- `RAG_CHUNK_OVERLAP`
- `RAG_TOP_K`
- `MEMORY_TOP_K`

## Error Shape

All expected application errors use:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "MODEL_NOT_FOUND",
    "message": "Requested model is not available in Ollama.",
    "details": {}
  }
}
```

## Health

`GET /api/health` returns app, version, environment, database, Ollama, and default-model status. It is used by the developer console to prove the full stack is reachable.
