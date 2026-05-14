# Contributor Notes

This repository is a local-first AI assistant platform. Keep changes focused on making the app easier to run, verify, and demonstrate.

## Priorities

1. Preserve a working local demo.
2. Keep the frontend, backend, SDK, docs, and tests aligned.
3. Prefer clear product behavior over speculative abstractions.
4. Keep runtime data and generated artifacts out of git.

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Pydantic, SQLAlchemy, SQLite, httpx
- Model runtime: Ollama
- Default model: `gemma4:e4b`
- SDK: Python

## Validation

Run these before publishing meaningful changes:

```powershell
cd D:\local_llm_test\backend
python -m pip install -e ".[dev]"

cd D:\local_llm_test
python -m unittest discover -s tests -p "test_*.py"

cd D:\local_llm_test\frontend
npm install
npm run build
```

## Boundaries

- Do not commit `.env`, `frontend/.env.local`, SQLite databases, uploaded files, `node_modules`, `.next`, virtual environments, or logs.
- Do not replace local Ollama as the default runtime with a cloud-only dependency.
- Keep the Ollama integration isolated so future adapters can be added cleanly.
