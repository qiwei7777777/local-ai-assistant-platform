# Architecture

## Product Goal

Local AI Assistant Platform turns a local Ollama model into a complete assistant product. It is intentionally more than a chat script: it includes a polished UI, a typed backend, persistence, retrieval, explicit memory, diagnostics, examples, tests, and a Python SDK.

## System Overview

```text
Browser
  -> Next.js app router frontend
    -> same-origin /api rewrite or direct backend URL
      -> FastAPI backend
        -> service layer
        -> repository layer
        -> SQLAlchemy models
        -> SQLite database
        -> local file storage
        -> Ollama HTTP API

Python scripts
  -> local_ai_assistant_sdk
    -> FastAPI backend
```

## Frontend

The frontend lives in `frontend/` and uses Next.js, React, TypeScript, Tailwind CSS, and small reusable UI primitives.

Core surfaces:

- Chat workspace for conversations, streaming, model selection, RAG selection, memory toggle, retry, and stop generation
- Knowledge-base page for file-backed retrieval workflows
- Memories page for explicit memory management
- Settings page for project configuration visibility
- Developer console for live diagnostics against `/api/health` and `/api/models`

The typed API client is centralized in `frontend/lib/api-client.ts`. Runtime configuration is centralized in `frontend/lib/config.ts`.

## Backend

The backend lives in `backend/` and uses FastAPI, Pydantic, SQLAlchemy, SQLite, and httpx.

Layer responsibilities:

- `api/`: route definitions and dependency injection
- `schemas/`: request and response DTOs
- `services/`: chat, model, health, file, retrieval, memory, and knowledge-base workflows
- `repositories/`: database access boundaries
- `models/`: SQLAlchemy ORM models
- `integrations/`: Ollama client and future model-runtime adapters
- `db/`: engine, session, and table initialization

Errors flow through `AppError` and the shared API response envelope, which keeps frontend error handling predictable.

## Chat Flow

1. Frontend or SDK sends `POST /api/chat` or `POST /api/chat/stream`.
2. Backend creates or loads the session.
3. User message is persisted in SQLite.
4. Optional explicit memories are searched and injected as system context.
5. Optional knowledge-base chunks are retrieved and injected as system context.
6. Backend calls Ollama with the selected model.
7. Assistant message is persisted.
8. Backend returns session, user message, assistant message, selected model, and retrieval/memory hit counts.

Streaming uses server-sent events:

- `chunk` for incremental assistant content
- `done` for the final persisted response payload
- `error` for classified failures

## Data Model

SQLite stores:

- Sessions
- Messages
- Uploaded file metadata
- Knowledge bases
- Knowledge-base file links
- Parsed chunks
- Explicit memories

Runtime data is intentionally local and ignored by git.

## RAG Boundary

The current retrieval implementation is deliberately lightweight. Uploaded documents are parsed into text, chunked, stored, and searched through a local scoring strategy. This keeps the project easy to run on any laptop while leaving a clear replacement boundary for vector databases or embedding models later.

## Demo Modes

Local mode:

- Frontend: `http://127.0.0.1:3000`
- Backend: `http://127.0.0.1:8000`
- Ollama: `http://127.0.0.1:11434`

LAN mode:

- Frontend and backend bind to `0.0.0.0`
- Browser can call either `/api` through Next.js or a direct LAN backend URL
- Backend CORS supports explicit origins and a LAN-friendly regex

External single-URL mode:

- `NEXT_PUBLIC_API_BASE_URL=/api`
- Next.js rewrites `/api/:path*` to local FastAPI
- Only frontend port `3000` needs to be exposed

## Extension Points

- Replace keyword retrieval with embeddings and a vector store
- Add an OpenAI-compatible model adapter beside `integrations/ollama.py`
- Persist user-facing settings through a backend settings endpoint
- Add tool-calling workflows for supported local models
- Add structured-output workflows for extraction and document automation

## Code Agent Workspace

The Code Agent layer adds a controlled developer-workbench surface:

```text
Frontend Code Agent page
  -> GET  /api/code-agent/workspace
  -> POST /api/code-agent/read
  -> POST /api/code-agent/plan
  -> POST /api/code-agent/command
Backend CodeAgentService
  -> bounded repository scan
  -> file read guardrails
  -> Ollama implementation planning
  -> command whitelist execution
```

This is deliberately review-first. The model can reason over selected files and produce patch-style guidance, but it cannot silently write files or run arbitrary shell commands.
