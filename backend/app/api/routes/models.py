from fastapi import APIRouter, Depends

from app.api.deps import get_model_service
from app.schemas.common import ApiResponse
from app.services.model_service import ModelService
from app.utils.responses import success_response


router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=ApiResponse)
def list_models(service: ModelService = Depends(get_model_service)) -> dict:
    return success_response(service.list_models().model_dump())
