from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_agent_service
from app.schemas.agent import AgentChatRequest
from app.schemas.common import ApiResponse
from app.services.agent_service import AgentService
from app.utils.responses import success_response

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def agent_chat(
    request: AgentChatRequest,
    service: AgentService = Depends(get_agent_service),
):
    result = service.run(request)
    return success_response(result.model_dump())
