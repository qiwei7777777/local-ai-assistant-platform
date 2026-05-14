from fastapi import APIRouter, Depends, status

from app.api.deps import get_session_service
from app.schemas.common import ApiResponse
from app.schemas.session import SessionCreateRequest, SessionUpdateRequest
from app.services.session_service import SessionService
from app.utils.responses import success_response


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=ApiResponse)
def list_sessions(service: SessionService = Depends(get_session_service)) -> dict:
    return success_response(service.list_sessions().model_dump(mode="json"))


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreateRequest,
    service: SessionService = Depends(get_session_service),
) -> dict:
    return success_response(service.create_session(payload).model_dump(mode="json"))


@router.patch("/{session_id}", response_model=ApiResponse)
def update_session(
    session_id: str,
    payload: SessionUpdateRequest,
    service: SessionService = Depends(get_session_service),
) -> dict:
    return success_response(service.update_session(session_id, payload).model_dump(mode="json"))


@router.delete("/{session_id}", response_model=ApiResponse)
def delete_session(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> dict:
    service.delete_session(session_id)
    return success_response({"deleted": True, "session_id": session_id})
