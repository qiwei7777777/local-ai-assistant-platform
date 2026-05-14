from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.api.deps import get_chat_service
from app.schemas.chat import ChatRequest
from app.schemas.common import ApiResponse
from app.services.chat_service import ChatService
from app.utils.responses import success_response


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def chat(payload: ChatRequest, service: ChatService = Depends(get_chat_service)) -> dict:
    return success_response(service.create_chat_completion(payload).model_dump(mode="json"))


@router.post("/stream", status_code=status.HTTP_200_OK)
def stream_chat(payload: ChatRequest, service: ChatService = Depends(get_chat_service)) -> StreamingResponse:
    return StreamingResponse(
        service.stream_chat_completion(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
