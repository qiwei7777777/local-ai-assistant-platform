from fastapi import APIRouter, Depends

from app.api.deps import get_health_service
from app.schemas.common import ApiResponse
from app.services.health_service import HealthService
from app.utils.responses import success_response


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=ApiResponse)
def healthcheck(service: HealthService = Depends(get_health_service)) -> dict:
    return success_response(service.get_status().model_dump())
