from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings
from app.core.constants import (
    FORBIDDEN_EXTENSIONS,
    FORBIDDEN_FILENAMES,
    IGNORED_DIRECTORIES,
    TEXT_EXTENSIONS,
)

DEFAULT_READ_LIMIT = 4000
MAX_READ_LIMIT = 12000
MAX_LIST_ENTRIES = 200
MAX_SEARCH_RESULTS = 50
MAX_LINE_LENGTH = 300


class AgentTools:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = settings.code_workspace_path
        self.max_read_file_bytes = settings.code_agent_max_file_bytes

    # ── 工具入口（供 AgentService 调用） ────────────────
    def get_tool_schemas(self) -> list[dict]:
        return [entry["schema"] for entry in self._registry().values()]

    def execute(self, name: str, arguments: dict) -> str:
        entry = self._registry().get(name)
        if entry is None:
            return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
        return str(entry["executor"](**arguments))

    # ── 工具实现 ───────────────────────────────────────
    def list_directory(self, path: str = ".") -> str:
        try:
            resolved = self._resolve_safe(path)
        except PermissionError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)

        if not resolved.is_dir():
            return json.dumps({"error": f"Not a directory: {path}"}, ensure_ascii=False)

        entries: list[dict] = []
        try:
            items = sorted(resolved.iterdir())
            for item in items:
                if self._is_ignored(item):
                    continue
                entry = {
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                }
                if item.is_file():
                    entry["size"] = item.stat().st_size
                    entry["extension"] = item.suffix
                entries.append(entry)
                if len(entries) >= MAX_LIST_ENTRIES:
                    break
        except OSError as exc:
            return json.dumps({"error": f"Cannot list directory: {exc}"}, ensure_ascii=False)

        return json.dumps(
            {"path": str(resolved.relative_to(self.root).as_posix() or "."),
             "entries": entries,
             "total": len(entries)},
            ensure_ascii=False,
        )

    def read_file(self, path: str, offset: int = 0,
                  limit: int = DEFAULT_READ_LIMIT) -> str:
        try:
            resolved = self._resolve_safe(path)
        except PermissionError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)
        if not resolved.is_file():
            return json.dumps({"error": f"File not found: {path}"}, ensure_ascii=False)
        if self._is_ignored(resolved):
            return json.dumps({"error": f"File is in an ignored directory: {path}"},
                              ensure_ascii=False)
        if self._is_forbidden_file(resolved):
            return json.dumps({"error": f"File is not readable for security reasons: {path}"},
                              ensure_ascii=False)
        if not self._is_text_file(resolved):
            return json.dumps({"error": f"Not a readable text file: {path}"},
                              ensure_ascii=False)

        file_size = resolved.stat().st_size
        if file_size > self.max_read_file_bytes:
            return json.dumps(
                {"error": f"File too large ({file_size} bytes, max {self.max_read_file_bytes}): {path}"},
                ensure_ascii=False,
            )

        offset = max(0, offset)
        limit = max(1, min(limit, MAX_READ_LIMIT))

        try:
            text = resolved.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return json.dumps({"error": f"Cannot read file: {exc}"}, ensure_ascii=False)

        snippet = text[offset : offset + limit]
        return json.dumps({
            "path": str(resolved.relative_to(self.root).as_posix()),
            "size": file_size,
            "offset": offset,
            "limit": limit,
            "returned": len(snippet),
            "content": snippet,
        }, ensure_ascii=False)

    def search_code(self, pattern: str, path: str = ".") -> str:
        try:
            resolved = self._resolve_safe(path)
        except PermissionError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)
        if not resolved.exists():
            return json.dumps({"error": f"Path not found: {path}"}, ensure_ascii=False)
        if not resolved.is_dir():
            files_to_search = [resolved]
        else:
            files_to_search: list[Path] = []
            for dirpath, dirnames, filenames in resolved.walk():
                dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRECTORIES]
                for fname in filenames:
                    fp = dirpath / fname
                    if self._is_ignored(fp):
                        continue
                    if self._is_forbidden_file(fp):
                        continue
                    if self._is_text_file(fp):
                        files_to_search.append(fp)

        matches: list[dict] = []
        for fp in files_to_search:
            if len(matches) >= MAX_SEARCH_RESULTS:
                break
            try:
                lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line_no, line in enumerate(lines, start=1):
                if len(matches) >= MAX_SEARCH_RESULTS:
                    break
                if pattern in line:
                    rel = str(fp.relative_to(self.root).as_posix())
                    truncated = line[:MAX_LINE_LENGTH]
                    matches.append({
                        "file": rel,
                        "line_number": line_no,
                        "line": truncated,
                    })

        return json.dumps({
            "pattern": pattern,
            "search_path": str(resolved.relative_to(self.root).as_posix() or "."),
            "matches": matches,
            "total_count": len(matches),
        }, ensure_ascii=False)

    # ── 安全辅助 ───────────────────────────────────────
    def _resolve_safe(self, raw_path: str) -> Path:
        workspace_root = self.root.resolve()
        p = Path(raw_path)

        if p.is_absolute():
            resolved = p.resolve()
        else:
            cleaned = raw_path.replace("\\", "/").strip().lstrip("/")
            if not cleaned:
                cleaned = "."
            resolved = (workspace_root / cleaned).resolve()

        try:
            resolved.relative_to(workspace_root)
        except ValueError:
            raise PermissionError(f"Path outside workspace: {raw_path}")
        return resolved

    def _is_ignored(self, path: Path) -> bool:
        try:
            parts = set(path.resolve().relative_to(self.root).parts)
        except ValueError:
            return True
        return bool(parts & IGNORED_DIRECTORIES)

    def _is_forbidden_file(self, path: Path) -> bool:
        if path.name in FORBIDDEN_FILENAMES:
            return True
        if path.suffix.lower() in FORBIDDEN_EXTENSIONS:
            return True
        return False

    def _is_text_file(self, path: Path) -> bool:
        suffix = path.suffix.lower()
        return suffix in TEXT_EXTENSIONS or path.name == ".gitignore"

    # ── 工具注册表（每次调用动态生成，绑定到 self） ────
    def _registry(self) -> dict:
        return {
            "list_directory": {
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "list_directory",
                        "description": "列出指定目录下的文件和子目录（跳过 .git/node_modules 等忽略目录）。返回文件名、类型、大小、扩展名。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "要列出的目录路径，相对于工作区根目录。使用 '.' 表示根目录。",
                                },
                            },
                            "required": ["path"],
                        },
                    },
                },
                "executor": self.list_directory,
            },
            "read_file": {
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "description": "读取文本文件的部分内容。默认返回前 4000 字符。可通过 offset/limit 分段读取。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "文件路径，相对于工作区根目录。",
                                },
                                "offset": {
                                    "type": "integer",
                                    "description": "从第几个字符开始读取（从 0 开始），默认 0。",
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "最多读取多少字符，默认 4000，最大 12000。",
                                },
                            },
                            "required": ["path"],
                        },
                    },
                },
                "executor": self.read_file,
            },
            "search_code": {
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "search_code",
                        "description": "在工作区代码中搜索关键词，返回匹配的文件路径、行号和行内容。支持限定搜索目录。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "pattern": {
                                    "type": "string",
                                    "description": "要搜索的关键词（子字符串匹配）。",
                                },
                                "path": {
                                    "type": "string",
                                    "description": "限定搜索的目录或文件路径，相对于工作区根目录。默认 '.' 搜索整个工作区。",
                                },
                            },
                            "required": ["pattern"],
                        },
                    },
                },
                "executor": self.search_code,
            },
        }
