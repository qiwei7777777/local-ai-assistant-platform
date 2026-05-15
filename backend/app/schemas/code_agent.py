from pydantic import BaseModel, Field


class CodeFileSummary(BaseModel):
    path: str
    name: str
    extension: str
    size: int
    modified_at: str


class CodeWorkspaceData(BaseModel):
    root: str
    files: list[CodeFileSummary]
    ignored_directories: list[str]
    allowed_commands: list[str]


class CodeFileData(BaseModel):
    path: str
    language: str
    size: int
    content: str


class CodeReadRequest(BaseModel):
    path: str = Field(min_length=1)


class CodePlanRequest(BaseModel):
    task: str = Field(min_length=1)
    file_paths: list[str] = Field(default_factory=list, max_length=8)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)


class CodePlanData(BaseModel):
    task: str
    model: str
    context_files: list[CodeFileData]
    plan: str


class CodeGeneratedFile(BaseModel):
    path: str = Field(min_length=1)
    content: str
    language: str = "text"
    action: str = "create"
    exists: bool = False


class CodeGenerateRequest(BaseModel):
    task: str = Field(min_length=1)
    target_directory: str = Field(default="generated", min_length=1)
    file_paths: list[str] = Field(default_factory=list, max_length=8)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)


class CodeGenerateData(BaseModel):
    task: str
    model: str
    target_directory: str
    files: list[CodeGeneratedFile]
    notes: str


class CodeWriteRequest(BaseModel):
    files: list[CodeGeneratedFile] = Field(min_length=1, max_length=12)
    overwrite: bool = False


class CodeWrittenFile(BaseModel):
    path: str
    bytes: int
    created: bool


class CodeWriteData(BaseModel):
    written_files: list[CodeWrittenFile]


class CodeCommandRequest(BaseModel):
    command: str = Field(min_length=1)


class CodeCommandData(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
