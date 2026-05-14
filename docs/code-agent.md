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
```

When the backend is started from `backend/`, the default `..` resolves to the repository root.

## Endpoints

```text
GET  /api/code-agent/workspace
POST /api/code-agent/read
POST /api/code-agent/plan
POST /api/code-agent/command
```

## Positioning

OpenClaw-style systems emphasize workspace state, tools, auditability, and agent actions. This project now demonstrates those ingredients in a scoped form suitable for local demos: repository context, model reasoning, safe command execution, and visible review output.
