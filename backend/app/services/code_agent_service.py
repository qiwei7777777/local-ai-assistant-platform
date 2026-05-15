from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from app.core.config import Settings
from app.core.constants import IGNORED_DIRECTORIES, TEXT_EXTENSIONS
from app.core.errors import AppError
from app.integrations.ollama import OllamaClient
from app.schemas.code_agent import (
    CodeCommandData,
    CodeFileData,
    CodeFileSummary,
    CodeGenerateData,
    CodeGeneratedFile,
    CodePlanData,
    CodeWorkspaceData,
    CodeWriteData,
    CodeWrittenFile,
)

ALLOWED_COMMANDS = {
    "git status --short",
    "git diff --stat",
    "git diff",
    "python -m unittest discover -s tests -p test_*.py",
    "npm run build --prefix frontend",
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
            timeout=self.settings.code_agent_model_timeout,
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

    def generate_files(
        self,
        *,
        task: str,
        target_directory: str,
        file_paths: list[str],
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
    ) -> CodeGenerateData:
        context_files = [self.read_file(path) for path in file_paths]
        selected_model = model or self.settings.ollama_default_model
        target_path = self._validate_target_directory(target_directory)
        prompt = self._build_file_generation_prompt(task, target_path, context_files)
        response = self.ollama_client.chat(
            model=selected_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful local coding agent. Generate complete text files for the user's task. "
                        "Return only valid JSON. Do not use Markdown fences. Do not claim files were already written."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature or 0.2,
            max_tokens=max_tokens or 4096,
            timeout=self.settings.code_agent_model_timeout,
        )
        raw = response.get("message", {}).get("content", "").strip()
        payload = self._parse_generation_payload(raw)
        files = [
            self._normalize_generated_file(item, target_path)
            for item in payload.get("files", [])
        ]
        if not files:
            raise AppError(
                message="The model did not return any files to write.",
                code="EMPTY_CODE_GENERATION",
                status_code=502,
            )
        return CodeGenerateData(
            task=task,
            model=selected_model,
            target_directory=target_path,
            files=files,
            notes=str(payload.get("notes", "")).strip(),
        )

    def write_files(self, files: list[CodeGeneratedFile], overwrite: bool) -> CodeWriteData:
        written_files: list[CodeWrittenFile] = []
        for item in files:
            file_path = self._resolve_writable_file(item.path)
            exists = file_path.exists()
            if exists and not overwrite:
                raise AppError(
                    message="Refusing to overwrite an existing file without confirmation.",
                    code="CODE_FILE_EXISTS",
                    status_code=409,
                    details={"path": item.path},
                )
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(item.content, encoding="utf-8", newline="\n")
            written_files.append(
                CodeWrittenFile(
                    path=self._relative_path(file_path),
                    bytes=file_path.stat().st_size,
                    created=not exists,
                )
            )
        return CodeWriteData(written_files=written_files)

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

    def _resolve_writable_file(self, path: str) -> Path:
        resolved = self._resolve_inside_root(path)
        if self._is_ignored(resolved):
            raise AppError(
                message="Refusing to write into an ignored workspace directory.",
                code="CODE_PATH_IGNORED",
                status_code=400,
                details={"path": path},
            )
        if not self._is_text_file(resolved):
            raise AppError(
                message="The code agent can only write readable text/code files.",
                code="CODE_FILE_NOT_WRITABLE",
                status_code=400,
                details={"path": path},
            )
        return resolved

    def _validate_target_directory(self, target_directory: str) -> str:
        normalized = target_directory.replace("\\", "/").strip().strip("/")
        if not normalized or normalized.startswith("../") or "/../" in f"/{normalized}/":
            raise AppError(
                message="Target directory must stay inside the configured workspace.",
                code="CODE_TARGET_DIRECTORY_INVALID",
                status_code=400,
                details={"target_directory": target_directory},
            )
        resolved = self._resolve_inside_root(normalized)
        if self._is_ignored(resolved):
            raise AppError(
                message="Target directory is ignored by the code agent.",
                code="CODE_PATH_IGNORED",
                status_code=400,
                details={"target_directory": target_directory},
            )
        return normalized

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

    def _parse_generation_payload(self, raw: str) -> dict:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise AppError(
                    message="The model did not return valid JSON file output.",
                    code="INVALID_CODE_GENERATION",
                    status_code=502,
                )
            try:
                payload = json.loads(raw[start : end + 1])
            except json.JSONDecodeError as exc:
                raise AppError(
                    message="The model did not return valid JSON file output.",
                    code="INVALID_CODE_GENERATION",
                    status_code=502,
                ) from exc
        if not isinstance(payload, dict):
            raise AppError(
                message="The model returned an invalid file generation payload.",
                code="INVALID_CODE_GENERATION",
                status_code=502,
            )
        return payload

    def _normalize_generated_file(self, item: object, target_directory: str) -> CodeGeneratedFile:
        if not isinstance(item, dict):
            raise AppError(
                message="Generated file entries must be JSON objects.",
                code="INVALID_CODE_GENERATION",
                status_code=502,
            )
        raw_path = str(item.get("path", "")).replace("\\", "/").strip().strip("/")
        if not raw_path:
            raise AppError(
                message="Generated file path is missing.",
                code="INVALID_CODE_GENERATION",
                status_code=502,
            )
        if not raw_path.startswith(f"{target_directory}/") and raw_path != target_directory:
            raw_path = f"{target_directory}/{raw_path}"
        file_path = self._resolve_writable_file(raw_path)
        content = str(item.get("content", ""))
        if len(content.encode("utf-8")) > self.settings.code_agent_max_file_bytes:
            raise AppError(
                message="Generated file exceeds the code agent write limit.",
                code="CODE_FILE_TOO_LARGE",
                status_code=413,
                details={"path": raw_path},
            )
        return CodeGeneratedFile(
            path=self._relative_path(file_path),
            content=content,
            language=str(item.get("language") or self._guess_language(file_path)),
            action="update" if file_path.exists() else "create",
            exists=file_path.exists(),
        )

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

    def _build_file_generation_prompt(
        self,
        task: str,
        target_directory: str,
        context_files: list[CodeFileData],
    ) -> str:
        context = "\n\n".join(
            f"--- FILE: {item.path} ({item.language}, {item.size} bytes) ---\n{item.content}"
            for item in context_files
        )
        if not context:
            context = "No existing files were selected."
        return (
            f"Task:\n{task}\n\n"
            f"Write all output files under this directory: {target_directory}\n\n"
            "Workspace context:\n"
            f"{context}\n\n"
            "Return exactly this JSON shape with complete file contents:\n"
            "{\n"
            '  "notes": "short explanation",\n'
            '  "files": [\n'
            '    {"path": "relative/path.ext", "language": "html", "content": "complete file content"}\n'
            "  ]\n"
            "}\n"
            "Use only relative paths. Prefer a small runnable project when the user asks for a page or app."
        )
