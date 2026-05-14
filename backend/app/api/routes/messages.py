from fastapi import APIRouter, Depends

from app.api.deps import get_session_service
from app.schemas.common import ApiResponse
from app.services.session_service import SessionService
from app.utils.responses import success_response


router = APIRouter(prefix="/sessions", tags=["messages"])


@router.get("/{session_id}/messages", response_model=ApiResponse)
def list_session_messages(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> dict:
    return success_response(service.list_messages(session_id).model_dump(mode="json"))
