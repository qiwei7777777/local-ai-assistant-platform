from fastapi import APIRouter, Depends

from app.api.deps import get_code_agent_service
from app.schemas.code_agent import (
    CodeCommandRequest,
    CodeGenerateRequest,
    CodePlanRequest,
    CodeReadRequest,
    CodeWriteRequest,
)
from app.schemas.common import ApiResponse
from app.services.code_agent_service import CodeAgentService
from app.utils.responses import success_response


router = APIRouter(prefix="/code-agent", tags=["code-agent"])


@router.get("/workspace", response_model=ApiResponse)
def inspect_workspace(service: CodeAgentService = Depends(get_code_agent_service)) -> dict:
    return success_response(service.inspect_workspace().model_dump())


@router.post("/read", response_model=ApiResponse)
def read_file(payload: CodeReadRequest, service: CodeAgentService = Depends(get_code_agent_service)) -> dict:
    return success_response(service.read_file(payload.path).model_dump())


@router.post("/plan", response_model=ApiResponse)
def create_plan(payload: CodePlanRequest, service: CodeAgentService = Depends(get_code_agent_service)) -> dict:
    return success_response(
        service.create_plan(
            task=payload.task,
            file_paths=payload.file_paths,
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        ).model_dump()
    )


@router.post("/generate", response_model=ApiResponse)
def generate_files(payload: CodeGenerateRequest, service: CodeAgentService = Depends(get_code_agent_service)) -> dict:
    return success_response(
        service.generate_files(
            task=payload.task,
            target_directory=payload.target_directory,
            file_paths=payload.file_paths,
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        ).model_dump()
    )


@router.post("/write", response_model=ApiResponse)
def write_files(payload: CodeWriteRequest, service: CodeAgentService = Depends(get_code_agent_service)) -> dict:
    return success_response(service.write_files(files=payload.files, overwrite=payload.overwrite).model_dump())


@router.post("/command", response_model=ApiResponse)
def run_command(payload: CodeCommandRequest, service: CodeAgentService = Depends(get_code_agent_service)) -> dict:
    return success_response(service.run_command(payload.command).model_dump())
