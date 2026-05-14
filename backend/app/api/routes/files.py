from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_file_service
from app.schemas.common import ApiResponse
from app.services.file_service import FileService
from app.utils.responses import success_response


router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=ApiResponse)
def list_files(service: FileService = Depends(get_file_service)) -> dict:
    return success_response(service.list_files().model_dump(mode="json"))


@router.post("/upload", response_model=ApiResponse)
async def upload_file(
    file: UploadFile = File(...),
    service: FileService = Depends(get_file_service),
) -> dict:
    data = await file.read()
    result = service.save_upload(
        filename=file.filename or "untitled",
        content_type=file.content_type,
        data=data,
    )
    return success_response(result.model_dump(mode="json"))
