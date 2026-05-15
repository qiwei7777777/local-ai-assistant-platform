# Tool-Calling Agent

The Agent feature (`AgentService`) implements a multi-turn tool-calling loop: the local model decides when to use tools, the service executes them against the workspace, and results feed back into the conversation until the model produces a final answer.

## How it differs from CodeAgentService

| | CodeAgentService | AgentService |
|---|---|---|
| Pattern | Single-turn: plan → generate → write | Multi-turn tool-calling loop |
| Tools | Fixed pipeline (read/plan/generate/write/command) | Dynamic tool registry (list_directory, read_file, search_code) |
| Output | Structured plan / file list / written files | Conversational answer + tool call audit trail |
| Iterations | N/A | Up to 5 loop iterations |

Both services share the same safety constants (`app.core.constants`) and workspace root.

## Architecture

```
POST /api/agent/chat
  → AgentService.run()
    → ollama_client.chat(messages, tools=[...])
      → if tool_calls: execute tool, append result, loop
      → if content: persist assistant message, return
    → max 5 iterations, then AGENT_MAX_ITERATIONS error
```

Each tool execution returns a JSON result string. The result is appended as a `role: "tool"` message in the Ollama conversation. Duration is measured per tool call.

## Available Tools

| Tool | Description | Required Args |
|---|---|---|
| `list_directory` | List files and subdirectories (skips ignored dirs) | `path` |
| `read_file` | Read text file content (offset/limit supported) | `path` |
| `search_code` | Search for a substring in workspace files | `pattern` |

## Safety Model

- **Path traversal protection:** All paths are resolved relative to `CODE_WORKSPACE_ROOT`. Absolute paths and `..` escapes are rejected.
- **Forbidden files:** `.env`, `.env.local`, `.env.production`, `*.key`, `*.pem`, `*.sqlite`, `*.db` are blocked from reads.
- **Ignored directories:** `.git`, `.next`, `.venv`, `.vscode`, `__pycache__`, `data`, `node_modules`, `uploads` are skipped.
- **File size limit:** Files exceeding `CODE_AGENT_MAX_FILE_BYTES` (default 120KB) are rejected.
- **Read limit:** `read_file` returns at most 12,000 characters per call.

## API

### POST /api/agent/chat

Request (`AgentChatRequest`):

```json
{
  "message": "What does the src/ directory contain?",
  "session_id": "optional-existing-session-uuid",
  "model": "gemma4:e4b",
  "temperature": 0.2,
  "max_tokens": 2048
}
```

Response (`AgentChatData`):

```json
{
  "session_id": "uuid",
  "user_message_id": "uuid",
  "assistant_message_id": "uuid",
  "model": "gemma4:e4b",
  "content": "The src/ directory contains...",
  "tool_calls_made": [
    {
      "tool_name": "list_directory",
      "arguments": {"path": "src"},
      "result_summary": "{\"path\": \"src\", \"entries\": [...], \"total\": 5}",
      "duration_ms": 2
    }
  ],
  "iterations": 2
}
```

Error codes: `SESSION_NOT_FOUND` (404), `AGENT_NO_RESPONSE` (502), `AGENT_MAX_ITERATIONS` (500).

The endpoint is non-streaming (blocking). With local models, expect 30-90 second response times depending on tool-call count and model speed.
