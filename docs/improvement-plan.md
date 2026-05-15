# Improvement Action Plan

Based on a full-stack audit conducted 2026-05-15. Every item below references actual
gaps found in the codebase. Follow these in order — each section is self-contained
enough to be done in a single sitting.

---

## 1. Extract shared safety constants (40 minutes)

**Problem:** `agent_tools.py` and `code_agent_service.py` each define their own
`IGNORED_DIRECTORIES` and `TEXT_EXTENSIONS`, and they don't agree:

| Constant | code_agent_service | agent_tools |
|---|---|---|
| IGNORED_DIRECTORIES | 7 entries | 8 entries (+`uploads`) |
| TEXT_EXTENSIONS | 15 entries | 16 entries (+`.cfg`) |

`agent_tools.py` also hardcodes `MAX_READ_FILE_BYTES = 120_000` instead of reading
`Settings.code_agent_max_file_bytes`.

**Action:**

1. Create a new file `backend/app/core/constants.py`:

```python
# Shared safety constants used by both CodeAgentService and AgentTools.
# Single source of truth — edit here, not in individual services.

IGNORED_DIRECTORIES: frozenset[str] = frozenset({
    ".git",
    ".next",
    ".venv",
    ".vscode",
    "__pycache__",
    "data",
    "node_modules",
    "uploads",
})

FORBIDDEN_FILENAMES: frozenset[str] = frozenset({
    ".env",
    ".env.local",
    ".env.production",
})

FORBIDDEN_EXTENSIONS: frozenset[str] = frozenset({
    ".key",
    ".pem",
    ".sqlite",
    ".db",
})

TEXT_EXTENSIONS: frozenset[str] = frozenset({
    ".cfg",
    ".css",
    ".env",
    ".example",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".ps1",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
})
```

2. Delete the duplicated constant blocks from both service files, replace with:
```python
from app.core.constants import (
    FORBIDDEN_EXTENSIONS,
    FORBIDDEN_FILENAMES,
    IGNORED_DIRECTORIES,
    TEXT_EXTENSIONS,
)
```

3. In `agent_tools.py`, remove `MAX_READ_FILE_BYTES = 120_000`. Accept `Settings`
   in the tool functions (or the class that holds them) and use
   `settings.code_agent_max_file_bytes` instead. Simplest approach: make
   `MAX_READ_FILE_BYTES` a global that gets set once at import time from `get_settings()`:
   ```python
   from app.core.config import get_settings
   MAX_READ_FILE_BYTES = get_settings().code_agent_max_file_bytes
   ```

4. Verify: `python -m pytest tests/test_agent_tools.py tests/test_backend_api.py -v`

---

## 2. Fill in missing `.env` settings (15 minutes)

**Problem:** `.env` is missing settings that `config.py` defines as defaults. They work
now because of Pydantic defaults, but the defaults are invisible to anyone configuring
the project.

**Action:** Add these lines to `d:\local_llm_test\.env`:

```env
CODE_WORKSPACE_ROOT=..
CODE_AGENT_MAX_FILE_BYTES=120000
CODE_AGENT_COMMAND_TIMEOUT=60
CODE_AGENT_MODEL_TIMEOUT=300
```

---

## 3. Fix the Next.js proxy timeout permanently (60 minutes)

**Problem:** In same-origin mode (`NEXT_PUBLIC_API_BASE_URL=/api`), the Next.js dev
server's built-in rewrite proxy kills requests at exactly 30 seconds. The code agent
generate endpoint takes 25-60 seconds depending on model speed and context size.
We papered over this by switching to direct mode (`.env.local` change), but that
forces CORS and prevents same-origin deployment.

**Action — custom server with configurable proxy timeout:**

1. Create `frontend/server.ts`:
```typescript
import { createServer } from "http";
import { parse } from "url";
import next from "next";
import { createProxyMiddleware } from "http-proxy-middleware";

const dev = process.env.NODE_ENV !== "production";
const hostname = "0.0.0.0";
const port = 3000;
const backendTarget =
  process.env.BACKEND_PROXY_TARGET?.trim() || "http://127.0.0.1:8000";

const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const proxy = createProxyMiddleware({
    target: backendTarget,
    changeOrigin: true,
    proxyTimeout: 300_000,   // 5 minutes — enough for any local model
    timeout: 300_000,
    pathFilter: ["/api/**"],
  });

  createServer((req, res) => {
    const parsedUrl = parse(req.url!, true);
    if (parsedUrl.pathname?.startsWith("/api/")) {
      proxy(req, res);
    } else {
      handle(req, res, parsedUrl);
    }
  }).listen(port, hostname, () => {
    console.log(`> Ready on http://${hostname}:${port}`);
  });
});
```

2. Install the dependency: `cd frontend && npm install http-proxy-middleware`
3. Install dev types: `npm install -D @types/http-proxy-middleware`
4. Update `frontend/package.json`:
```json
"scripts": {
  "dev": "tsx server.ts",
  ...
}
```
5. Install `tsx`: `npm install -D tsx`
6. Revert `frontend/.env.local`:
```env
NEXT_PUBLIC_API_BASE_URL=/api
```
7. Kill old frontend, restart: `npm run dev`
8. Verify: `curl -X POST http://127.0.0.1:3000/api/code-agent/generate ...` completes
   in 60+ seconds without 500.

---

## 4. Build the Agent chat frontend (3-4 hours)

**Problem:** `AgentService`, `/api/agent/chat`, and three tools (list_directory,
read_file, search_code) are built and tested. But there is zero frontend UI.
The code-agent page uses `CodeAgentService` (plan/generate/write), not `AgentService`.

**Action — create a new page at `frontend/app/agent/page.tsx`:**

1. Add Agent types to `frontend/types/api.ts` first:
```typescript
export interface AgentToolCall {
  name: string;
  arguments: Record<string, unknown>;
}

export interface AgentToolCallRecord {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown> | null;
  duration_ms: number;
}

export interface AgentChatData {
  session_id: number;
  session_title: string;
  user_message_id: number;
  assistant_message_id: number;
  assistant_content: string;
  model: string;
  tool_calls: AgentToolCallRecord[];
  total_duration_ms: number;
}
```

2. Add API client methods in `frontend/lib/api-client.ts`:
```typescript
agentChat(payload: {
  message: string;
  session_id?: number;
  session_title?: string;
  system_prompt?: string;
  model?: string;
  tools?: AgentToolCall[];
}) {
  return request<AgentChatData>("/api/agent/chat", {
    method: "POST",
    timeoutMs: CODE_AGENT_REQUEST_TIMEOUT_MS,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
},
```

3. Build `frontend/components/agent/agent-workspace.tsx`. The component needs:
   - Chat input + message history display (reuse patterns from `chat-workspace.tsx`)
   - Tool call expand/collapse panel showing arguments, result, and duration
   - Session management (create new, continue existing)
   - Loading state while agent is running (could be 30-90 seconds with gemma4)
   - Empty state, error state, retry

4. Wire the new page into `frontend/components/app-shell.tsx` navigation.

---

## 5. Add missing tests (2 hours)

**Problem:** Specific scenarios are untested.

**Action — add these test cases to the existing test files:**

In `tests/test_backend_api.py`:
- `test_code_agent_file_too_large` — create a temp file >120KB, assert 413
- `test_code_agent_workspace_not_found` — set `CODE_WORKSPACE_ROOT` to a
  nonexistent path, assert 500
- `test_code_agent_overwrite_existing_refused` — write a file, then write again
  without overwrite flag, assert 409

In `tests/test_agent_api.py`:
- `test_agent_max_iterations_exceeded` — use `NeverToolFakeOllamaClient` (already
  exists in the file, check if it's used for this case)
- `test_agent_unknown_tool_fallback` — model calls a tool not in the list,
  assert graceful handling
- `test_agent_session_continuation` — send a second message to the same session,
  assert history is included

In a new file `frontend/__tests__/api-client.test.ts`:
- Test `generateCodeFiles` request/response shape parsing
- Test timeout behavior (mock fetch with AbortController)
- Test invalid JSON response → `INVALID_RESPONSE` error

---

## 6. Update documentation (90 minutes)

**Problem:** Docs are behind the code. Specific things to fix:

| File | What's missing |
|---|---|
| `docs/code-agent.md` | `/generate` and `/write` endpoints, `CODE_AGENT_MODEL_TIMEOUT` env var |
| `docs/project-roadmap.md` | "Next" item 4 (tool-calling) is partially done; add Agent section to Completed |
| No file | `/api/agent/chat` endpoint has zero documentation |

**Action:**

1. `docs/code-agent.md` — add sections for:
   - `POST /api/code-agent/generate` (request shape, response shape, JSON output format)
   - `POST /api/code-agent/write` (request shape, overwrite flag behavior)
   - Environment variable: `CODE_AGENT_MODEL_TIMEOUT` (default 300s)

2. Create `docs/agent.md` documenting:
   - Architecture: tool-calling loop, max 5 iterations, session persistence
   - Three available tools (list_directory, read_file, search_code)
   - Safety model: path traversal protection, forbidden files, ignored dirs, size limits
   - API: `POST /api/agent/chat` request/response schema
   - How it differs from `CodeAgentService` (tool loop vs. single-turn plan/generate)

3. `docs/project-roadmap.md`:
   - Move "item 4: tool-calling workflows" to Completed
   - Add "item 9: Agent streaming support"
   - Add "item 10: Agent frontend UI"

---

## 7. Complete the SDK (2 hours)

**Problem:** `sdk/python/src/local_ai_assistant_sdk/client.py` is missing:
- All code-agent methods (workspace, read_file, plan, generate_files, write_files, run_command)
- Agent chat method
- Streaming support for chat

**Action:**

1. Add types to `sdk/python/src/local_ai_assistant_sdk/types.py`:
```python
@dataclass
class CodeFileSummary:
    path: str
    name: str
    extension: str
    size: int
    modified_at: str

# ... (all CodeAgent and Agent types from the backend schemas)
```

2. Add methods to `client.py`:
```python
def inspect_code_workspace(self) -> CodeWorkspaceData: ...
def read_code_file(self, path: str) -> CodeFileData: ...
def create_code_plan(self, task: str, file_paths: list[str], ...) -> CodePlanData: ...
def generate_code_files(self, task: str, target_directory: str, ...) -> CodeGenerateData: ...
def write_code_files(self, files: list, overwrite: bool = False) -> CodeWriteData: ...
def run_code_command(self, command: str) -> CodeCommandData: ...
def agent_chat(self, message: str, ...) -> AgentChatData: ...
```

3. Write `tests/test_sdk_code_agent.py` using `httpx.MockTransport` (same pattern as
   `test_sdk_client.py`).

---

## 8. Config consolidation — `agent_tools.py` reads from Settings (30 minutes)

**Problem:** `agent_tools.py` line 27: `MAX_READ_FILE_BYTES = 120_000` is hardcoded.
If someone changes `CODE_AGENT_MAX_FILE_BYTES` in `.env`, the agent tools won't
respect it.

**Action:**

The tool functions in `agent_tools.py` are currently standalone functions. Wrap them
in a class that receives `Settings` at construction time, matching the pattern used
by every other service:

```python
class AgentTools:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = settings.code_workspace_path

    def list_directory(self, path: str = ".") -> str: ...
    def read_file(self, path: str, limit: int = DEFAULT_READ_LIMIT) -> str: ...
    def search_code(self, path: str, pattern: str) -> str: ...

    # Internal helpers use self.settings.code_agent_max_file_bytes
    # and self.root instead of module-level paths.
```

Then update `AgentService.__init__` to construct `AgentTools(settings)` and
`get_agent_service` in `deps.py` to pass settings through.

---

## 9. Minor polish items (60 minutes total)

These are small enough to batch together:

1. **Add logging to `chat_service.py`** — the `except Exception: rollback; raise` on
   line ~340 silently swallows error context. Add:
   ```python
   import logging
   logger = logging.getLogger(__name__)
   # in the except block:
   logger.exception("Chat completion failed, rolling back transaction")
   ```

2. **Add `version` and `environment` fields** to `sdk/types.py` `HealthStatus` —
   they're returned by the backend but missing from the SDK type.

3. **Fix `RetrievalHit.score` type** in `sdk/types.py` — change from `int` to `float`.

4. **Use shared `ErrorState` component** in `code-agent-workspace.tsx` — the inline
   error div at line 274 duplicates what `ErrorState` already provides.

5. **Add `CODE_AGENT_MODEL_TIMEOUT=300` comment** to `.env.example` so new users
   know the setting exists.

---

## Execution order

If you do these in order, each one builds on the previous without conflicts:

```
Day 1 (2h):  #1 Constants + #2 .env + #8 Config consolidation
Day 2 (3h):  #3 Custom server (proxy timeout fix)
Day 3 (4h):  #4 Agent frontend
Day 4 (2h):  #5 Missing tests + #6 Documentation
Day 5 (2h):  #7 SDK completion + #9 Polish
```
