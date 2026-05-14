from fastapi import APIRouter, Depends

from app.api.deps import get_knowledge_base_service, get_retrieval_service
from app.schemas.common import ApiResponse
from app.schemas.retrieval import RetrievalSearchRequest
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.retrieval_service import RetrievalService
from app.utils.responses import success_response


router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=ApiResponse)
def search_knowledge_base(
    payload: RetrievalSearchRequest,
    knowledge_base_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> dict:
    knowledge_base_service.get_knowledge_base_or_error(payload.knowledge_base_id)
    chunks = knowledge_base_service.knowledge_base_repository.list_chunks(payload.knowledge_base_id)
    result = retrieval_service.search(
        knowledge_base_id=payload.knowledge_base_id,
        query=payload.query,
        chunks=chunks,
        top_k=payload.top_k,
    )
    return success_response(result.model_dump(mode="json"))
