from fastapi import APIRouter

from app.api.routes.agent import router as agent_router
from app.api.routes.chat import router as chat_router
from app.api.routes.code_agent import router as code_agent_router
from app.api.routes.files import router as files_router
from app.api.routes.health import router as health_router
from app.api.routes.knowledge_bases import router as knowledge_bases_router
from app.api.routes.memories import router as memories_router
from app.api.routes.messages import router as messages_router
from app.api.routes.models import router as models_router
from app.api.routes.retrieval import router as retrieval_router
from app.api.routes.sessions import router as sessions_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(chat_router)
api_router.include_router(agent_router)
api_router.include_router(code_agent_router)
api_router.include_router(sessions_router)
api_router.include_router(messages_router)
api_router.include_router(files_router)
api_router.include_router(knowledge_bases_router)
api_router.include_router(retrieval_router)
api_router.include_router(memories_router)
