# Roadmap

## Completed

- Local Ollama-backed chat
- Multi-session persistence
- Streaming and non-streaming chat modes
- Stop generation handling
- Model list and model switching
- File upload and parsing
- Knowledge bases and local retrieval
- Explicit memory
- Developer diagnostics
- Code Agent workspace with repository inspection, file context, AI implementation planning, file generation, file writing, and safe validation commands
- Tool-calling Agent with multi-turn loop, workspace tools (list_directory, read_file, search_code), session persistence, and frontend UI
- Python SDK
- Windows startup scripts
- Regression tests and frontend build validation

## Next

1. Add guarded patch application with human approval.
2. Add OpenAI-compatible adapter support for Ollama `/v1` and optional remote providers.
3. Add structured-output workflows for extraction and report generation.
4. Add Agent streaming support (SSE with tool-call progress events).
5. Replace keyword retrieval with embeddings and a vector store.
6. Add conversation export for project-management reports and portfolio demos.
7. Add persisted user settings.
8. Add Docker Compose for cross-platform setup.
