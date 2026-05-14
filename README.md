# Local AI Assistant Platform

A local-first AI assistant workspace built with Next.js, FastAPI, SQLite, and Ollama. The project is designed as a portfolio-ready product demo: it runs on a laptop, supports LAN sharing, persists conversations locally, and exposes knowledge-base retrieval plus explicit memory without depending on a cloud LLM service.

## Highlights

- Local model runtime through Ollama, defaulting to `gemma4:e4b`
- Chat workspace with multi-session history, model switching, Markdown rendering, streaming, and stop-generation handling
- FastAPI backend with typed schemas, service/repository layering, unified error responses, and OpenAPI docs
- SQLite persistence for sessions, messages, uploaded files, knowledge bases, chunks, and memories
- Lightweight RAG over uploaded text, Markdown, PDF, and Word files
- Explicit long-term memory that can be enabled per chat request
- Python SDK and runnable examples for automation or integration demos
- LAN-friendly configuration plus same-origin `/api` proxy mode for simple public demos through tools such as ngrok
- Developer console that checks backend health, model availability, API routing mode, app version, and environment

## Why This Project Matters

Local AI products are moving from single-machine scripts toward complete, inspectable applications. Ollama now supports streaming, structured outputs, tools, and an OpenAI-compatible API surface, which makes local models easier to integrate into production-style apps. Google released Gemma 4 on April 2, 2026 as a new open-model family focused on capable edge deployment. This project packages that direction into a small but complete product: UI, backend, storage, retrieval, memory, SDK, docs, and tests.

Research notes and sources are captured in [docs/market-research.md](docs/market-research.md).

## Architecture

```text
Next.js frontend
  -> /api proxy or direct FastAPI URL
FastAPI backend
  -> service / repository / schema / integration layers
  -> SQLite local database
  -> local file and chunk storage
  -> Ollama chat API
Python SDK
  -> typed client wrappers for backend APIs
```

More detail: [docs/architecture.md](docs/architecture.md).

## Repository Layout

```text
backend/      FastAPI app, SQLAlchemy models, services, repositories, schemas
frontend/     Next.js app router UI, typed API client, shared components
sdk/python/   Python SDK package
examples/     SDK quickstarts and feature demos
scripts/      Windows development, smoke-test, and stack startup helpers
tests/        Backend and SDK regression tests
docs/         Architecture, runbook, module notes, and market research
```

## Prerequisites

- Windows PowerShell
- Python 3.11+
- Node.js 20+
- Ollama installed and running
- A local model pulled with Ollama:

```powershell
ollama pull gemma4:e4b
```

You can switch to any installed Ollama model from the UI model dropdown.

## Quick Start

1. Prepare environment files:

```powershell
Copy-Item D:\local_llm_test\.env.example D:\local_llm_test\.env
Copy-Item D:\local_llm_test\frontend\.env.example D:\local_llm_test\frontend\.env.local
```

2. Start the backend:

```powershell
powershell -ExecutionPolicy Bypass -File D:\local_llm_test\scripts\dev-backend.ps1
```

3. Start the frontend:

```powershell
powershell -ExecutionPolicy Bypass -File D:\local_llm_test\scripts\dev-frontend.ps1
```

4. Open the app:

```text
Frontend: http://127.0.0.1:3000
Backend:  http://127.0.0.1:8000
OpenAPI:  http://127.0.0.1:8000/docs
```

## LAN and Demo Modes

The default frontend demo mode is same-origin:

```env
NEXT_PUBLIC_API_BASE_URL=/api
BACKEND_PROXY_TARGET=http://127.0.0.1:8000
```

This lets the frontend call `/api/...` while Next.js proxies to FastAPI. It is the easiest mode for ngrok or a single shared URL.

For direct LAN access, set:

```env
NEXT_PUBLIC_API_BASE_URL=http://<your-lan-ip>:8000
```

Then add the frontend origin to root `.env`:

```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://<your-lan-ip>:3000
```

The backend and frontend dev scripts both bind to `0.0.0.0`, so other devices on the same network can reach them if the firewall allows it.

## Validation

Install backend dependencies and run tests:

```powershell
cd D:\local_llm_test\backend
python -m pip install -e ".[dev]"
cd D:\local_llm_test
python -m unittest discover -s tests -p "test_*.py"
```

Build the frontend:

```powershell
cd D:\local_llm_test\frontend
npm install
npm run build
```

Run the full smoke script:

```powershell
powershell -ExecutionPolicy Bypass -File D:\local_llm_test\scripts\smoke-test.ps1
```

## Portfolio Talking Points

- Product thinking: transforms a local model into a full assistant platform with sessions, memory, RAG, diagnostics, and SDK access
- Engineering thinking: separates frontend, backend, SDK, data, integrations, tests, and runbooks
- Operations thinking: supports local, LAN, and single-URL external demo modes
- Reliability thinking: typed API contracts, explicit errors, stream timeout handling, abort handling, and regression tests

## Useful Endpoints

```text
GET  /api/health
GET  /api/models
POST /api/chat
POST /api/chat/stream
GET  /api/sessions
POST /api/files/upload
POST /api/knowledge-bases
POST /api/retrieval/search
POST /api/memories
```

## Status

Version: `1.2.0`

This repository is ready for GitHub portfolio display after running the validation commands above. Local runtime data, logs, virtual environments, `node_modules`, build output, and SQLite data are excluded by `.gitignore`.
