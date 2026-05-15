from __future__ import annotations

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
