from fastapi import APIRouter, Depends, status

from app.api.deps import get_memory_service
from app.schemas.common import ApiResponse
from app.schemas.memory import MemoryCreateRequest
from app.services.memory_service import MemoryService
from app.utils.responses import success_response


router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("", response_model=ApiResponse)
def list_memories(service: MemoryService = Depends(get_memory_service)) -> dict:
    return success_response(service.list_memories().model_dump(mode="json"))


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_memory(
    payload: MemoryCreateRequest,
    service: MemoryService = Depends(get_memory_service),
) -> dict:
    return success_response(service.create_memory(payload).model_dump(mode="json"))


@router.delete("/{memory_id}", response_model=ApiResponse)
def delete_memory(
    memory_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> dict:
    service.delete_memory(memory_id)
    return success_response({"deleted": True, "memory_id": memory_id})
