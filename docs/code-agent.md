# Code Agent

The Code Agent feature moves the project closer to modern agentic coding tools while keeping a safe, portfolio-friendly boundary.

## Capabilities

- Inspect the configured repository workspace
- Search and preview readable source files
- Select up to eight files as model context
- Ask the local model for an implementation plan and patch-style guidance
- Run a small set of whitelisted validation commands
- Display command exit code, duration, stdout, and stderr

## Safety Boundaries

- Workspace is limited to `CODE_WORKSPACE_ROOT`
- Path traversal outside the workspace is blocked
- Generated and sensitive directories are ignored
- Large files are rejected by `CODE_AGENT_MAX_FILE_BYTES`
- Shell access is not arbitrary; commands must match the whitelist in `CodeAgentService`
- AI output is advisory and review-first, not silent file mutation

## Environment

```env
CODE_WORKSPACE_ROOT=..
CODE_AGENT_MAX_FILE_BYTES=120000
CODE_AGENT_COMMAND_TIMEOUT=60
CODE_AGENT_MODEL_TIMEOUT=300
```

`CODE_AGENT_MODEL_TIMEOUT` (default 300s) controls how long the service waits for the local model to produce a plan or file generation response.

When the backend is started from `backend/`, the default `..` resolves to the repository root.

## Endpoints

```text
GET  /api/code-agent/workspace   — list workspace files, ignored dirs, allowed commands
POST /api/code-agent/read        — read a single file (body: {path})
POST /api/code-agent/plan        — generate an implementation plan (body: {task, file_paths, model?})
POST /api/code-agent/generate    — generate file drafts as structured JSON (body: {task, target_directory, file_paths, model?})
POST /api/code-agent/write       — write generated files to disk (body: {files, overwrite?})
POST /api/code-agent/command     — run a whitelisted command (body: {command})
```

### POST /api/code-agent/generate

Asks the model to produce new files as structured JSON. Request body:

```json
{
  "task": "Create a tiny static HTML page.",
  "target_directory": "agent-output/demo",
  "file_paths": [],
  "model": "gemma4:e4b"
}
```

Response (`CodeGenerateData`): `{task, model, target_directory, files: [{path, content, language, action, exists}], notes}`.

The model is prompted to return `{"notes": "...", "files": [{"path": "...", "language": "...", "content": "..."}]}`. The service parses this JSON (with fallback extraction from markdown fences or raw output) and normalises all paths under `target_directory`.

### POST /api/code-agent/write

Writes previously generated (and reviewed) files to disk. Request body:

```json
{
  "files": [{"path": "agent-output/demo/index.html", "content": "<!doctype html>...", "language": "html"}],
  "overwrite": false
}
```

If `overwrite` is `false` (default) and the file already exists, the endpoint returns `409 CODE_FILE_EXISTS`. Set `overwrite: true` to replace existing files. Each file path is validated against workspace boundaries and ignored-directory rules before writing.

## Positioning

OpenClaw-style systems emphasize workspace state, tools, auditability, and agent actions. This project now demonstrates those ingredients in a scoped form suitable for local demos: repository context, model reasoning, safe command execution, and visible review output.
