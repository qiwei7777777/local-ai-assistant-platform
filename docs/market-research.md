# Market Research Notes

## Summary

The project fits a visible 2026 direction: local models are becoming practical product infrastructure rather than novelty demos. Ollama provides a developer-friendly local runtime with streaming, structured outputs, tools, and OpenAI-compatible endpoints. Google positions Gemma 4 as a capable open model family for edge deployment. A portfolio project that combines local inference, a real UI, persistence, retrieval, memory, diagnostics, and SDK access is stronger than a single chat page because it demonstrates product and engineering maturity.

## Sources Checked

- Google Developers Blog, April 2, 2026: "Bring state-of-the-art agentic skills to the edge with Gemma 4"  
  https://developers.googleblog.com/bring-state-of-the-art-agentic-skills-to-the-edge-with-gemma-4/
- Google Blog, "Gemma 4: Our most capable open models to date"  
  https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/
- Ollama documentation, OpenAI compatibility  
  https://docs.ollama.com/openai
- Ollama documentation, Streaming  
  https://docs.ollama.com/capabilities/streaming
- Ollama Blog, "Streaming responses with tool calling", May 28, 2025  
  https://ollama.com/blog/streaming-tool
- Ollama Blog, "Structured outputs", December 6, 2024  
  https://ollama.com/blog/structured-outputs

## Relevant Trends

### Local-first AI

Local inference is attractive for demos and applied workflows because data stays on the user's machine, latency can be predictable after model load, and the app remains useful without cloud model keys. This project leans into that by using Ollama, SQLite, and local file storage.

### OpenAI-compatible local runtimes

Ollama's OpenAI-compatible API lowers integration friction because many tools already speak Chat Completions or Responses-style APIs. The current project uses Ollama's native chat endpoint, but the integration boundary is isolated in `backend/app/integrations/ollama.py`, so a future OpenAI-compatible adapter is straightforward.

### Streaming UX

Streaming is now expected in chat products. The project supports server-sent events, first-token timeout handling, idle timeout handling, and stop generation. That makes it feel more like a real assistant than a blocking request form.

### Tool calling and structured outputs

Ollama supports structured outputs and streaming tool calls for supported models. This project already has RAG, file handling, and memory. The next logical product step is turning those capabilities into model-callable tools or structured extraction workflows.

### Edge-capable Gemma models

Gemma 4 strengthens the story for running capable models close to the user. The project default `gemma4:e4b` is therefore a good portfolio choice: it communicates current local-model awareness while keeping the demo runnable on ordinary hardware.

## Upgrade Decisions Applied

- Position the repository as a complete local AI assistant platform instead of a temporary model test.
- Keep the Ollama integration isolated to preserve future OpenAI-compatible adapter options.
- Improve diagnostics by exposing app version and environment in `/api/health`.
- Document local, LAN, and single-URL demo modes clearly for reviewers.
- Remove hardcoded private LAN IPs from examples.
- Rewrite README and architecture docs in clean English for GitHub display.

## Product Roadmap

1. Add an OpenAI-compatible model adapter for local Ollama `/v1` and remote providers.
2. Add structured-output workflows for file extraction and report generation.
3. Add tool-calling for retrieval, memory lookup, and file search.
4. Replace keyword retrieval with an embedding-backed vector store.
5. Add exportable conversation artifacts for portfolio and project-management demos.
