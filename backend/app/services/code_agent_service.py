from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from app.core.config import Settings
from app.core.errors import AppError
from app.integrations.ollama import OllamaClient
from app.schemas.code_agent import CodeCommandData, CodeFileData, CodeFileSummary, CodePlanData, CodeWorkspaceData


IGNORED_DIRECTORIES = {
    ".git",
    ".next",
    ".venv",
    ".vscode",
    "__pycache__",
    "data",
    "node_modules",
}
ALLOWED_COMMANDS = {
    "git status --short",
    "git diff --stat",
    "git diff",
    "python -m unittest discover -s tests -p test_*.py",
    "npm run build --prefix frontend",
}
TEXT_EXTENSIONS = {
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
}


class CodeAgentService:
    def __init__(self, settings: Settings, ollama_client: OllamaClient) -> None:
        self.settings = settings
        self.ollama_client = ollama_client
        self.root = settings.code_workspace_path

    def inspect_workspace(self) -> CodeWorkspaceData:
        self._ensure_root_exists()
        files: list[CodeFileSummary] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [dirname for dirname in dirnames if dirname not in IGNORED_DIRECTORIES]
            current_dir = Path(dirpath)
            for filename in filenames:
                path = current_dir / filename
                if not path.is_file() or not self._is_text_file(path):
                    continue
                stat = path.stat()
                files.append(
                    CodeFileSummary(
                        path=self._relative_path(path),
                        name=path.name,
                        extension=path.suffix,
                        size=stat.st_size,
                        modified_at=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)),
                    )
                )

        files.sort(key=lambda item: item.path)
        return CodeWorkspaceData(
            root=str(self.root),
            files=files[:500],
            ignored_directories=sorted(IGNORED_DIRECTORIES),
            allowed_commands=sorted(ALLOWED_COMMANDS),
        )

    def read_file(self, path: str) -> CodeFileData:
        file_path = self._resolve_inside_root(path)
        if not file_path.is_file():
            raise AppError(
                message="Requested path is not a file.",
                code="CODE_FILE_NOT_FOUND",
                status_code=404,
                details={"path": path},
            )
        if self._is_ignored(file_path) or not self._is_text_file(file_path):
            raise AppError(
                message="Requested file is not readable by the code agent.",
                code="CODE_FILE_NOT_READABLE",
                status_code=400,
                details={"path": path},
            )
        size = file_path.stat().st_size
        if size > self.settings.code_agent_max_file_bytes:
            raise AppError(
                message="Requested file exceeds the code agent read limit.",
                code="CODE_FILE_TOO_LARGE",
                status_code=413,
                details={"path": path, "size": size},
            )
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return CodeFileData(
            path=self._relative_path(file_path),
            language=self._guess_language(file_path),
            size=size,
            content=content,
        )

    def create_plan(
        self,
        *,
        task: str,
        file_paths: list[str],
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
    ) -> CodePlanData:
        context_files = [self.read_file(path) for path in file_paths]
        selected_model = model or self.settings.ollama_default_model
        prompt = self._build_code_prompt(task, context_files)
        response = self.ollama_client.chat(
            model=selected_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior coding agent. Produce a practical implementation plan, "
                        "identify files to change, call out risks, and include focused code snippets or unified diffs. "
                        "Do not claim to have edited files."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature or 0.2,
            max_tokens=max_tokens or 2048,
        )
        plan = response.get("message", {}).get("content", "").strip()
        if not plan:
            raise AppError(
                message="The model returned an empty code plan.",
                code="EMPTY_CODE_PLAN",
                status_code=502,
            )
        return CodePlanData(
            task=task,
            model=selected_model,
            context_files=context_files,
            plan=plan,
        )

    def run_command(self, command: str) -> CodeCommandData:
        normalized = " ".join(command.strip().split())
        if normalized not in ALLOWED_COMMANDS:
            raise AppError(
                message="Command is not allowed by the code agent sandbox.",
                code="CODE_COMMAND_NOT_ALLOWED",
                status_code=400,
                details={"command": command, "allowed_commands": sorted(ALLOWED_COMMANDS)},
            )

        start = time.perf_counter()
        completed = subprocess.run(
            normalized,
            cwd=self.root,
            shell=True,
            capture_output=True,
            text=True,
            timeout=self.settings.code_agent_command_timeout,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        return CodeCommandData(
            command=normalized,
            exit_code=completed.returncode,
            stdout=completed.stdout[-12_000:],
            stderr=completed.stderr[-12_000:],
            duration_ms=duration_ms,
        )

    def _ensure_root_exists(self) -> None:
        if not self.root.exists() or not self.root.is_dir():
            raise AppError(
                message="Code workspace root does not exist.",
                code="CODE_WORKSPACE_NOT_FOUND",
                status_code=500,
                details={"root": str(self.root)},
            )

    def _resolve_inside_root(self, path: str) -> Path:
        resolved = (self.root / path).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise AppError(
                message="Path is outside the configured code workspace.",
                code="CODE_PATH_OUTSIDE_WORKSPACE",
                status_code=400,
                details={"path": path},
            ) from exc
        return resolved

    def _relative_path(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def _is_ignored(self, path: Path) -> bool:
        parts = set(path.relative_to(self.root).parts)
        return bool(parts & IGNORED_DIRECTORIES)

    def _is_text_file(self, path: Path) -> bool:
        return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {".gitignore", "README.md"}

    def _guess_language(self, path: Path) -> str:
        return {
            ".css": "css",
            ".js": "javascript",
            ".json": "json",
            ".md": "markdown",
            ".ps1": "powershell",
            ".py": "python",
            ".toml": "toml",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".yml": "yaml",
            ".yaml": "yaml",
        }.get(path.suffix.lower(), "text")

    def _build_code_prompt(self, task: str, context_files: list[CodeFileData]) -> str:
        context = "\n\n".join(
            f"--- FILE: {item.path} ({item.language}, {item.size} bytes) ---\n{item.content}"
            for item in context_files
        )
        if not context:
            context = "No files were selected. Ask for file context if needed."
        return (
            f"Task:\n{task}\n\n"
            "Workspace context:\n"
            f"{context}\n\n"
            "Respond with: 1) diagnosis, 2) implementation plan, 3) exact files to edit, "
            "4) suggested patch/code snippets, 5) validation commands."
        )
