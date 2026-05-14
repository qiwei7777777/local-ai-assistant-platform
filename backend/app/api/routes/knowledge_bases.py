from fastapi import APIRouter, Depends, status

from app.api.deps import get_knowledge_base_service
from app.schemas.common import ApiResponse
from app.schemas.knowledge_base import (
    KnowledgeBaseAttachFileRequest,
    KnowledgeBaseCreateRequest,
)
from app.services.knowledge_base_service import KnowledgeBaseService
from app.utils.responses import success_response


router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=ApiResponse)
def list_knowledge_bases(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> dict:
    return success_response(service.list_knowledge_bases().model_dump(mode="json"))


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    payload: KnowledgeBaseCreateRequest,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> dict:
    return success_response(service.create_knowledge_base(payload).model_dump(mode="json"))


@router.post("/{knowledge_base_id}/files", response_model=ApiResponse)
def add_file_to_knowledge_base(
    knowledge_base_id: str,
    payload: KnowledgeBaseAttachFileRequest,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> dict:
    return success_response(
        service.attach_file(knowledge_base_id, payload).model_dump(mode="json")
    )


@router.get("/{knowledge_base_id}/files", response_model=ApiResponse)
def list_knowledge_base_files(
    knowledge_base_id: str,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> dict:
    return success_response(service.list_files(knowledge_base_id).model_dump(mode="json"))
