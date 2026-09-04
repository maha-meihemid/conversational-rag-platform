from fastapi import APIRouter

from app.api.routes.assistant_profile import router as assistant_profile_router
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(assistant_profile_router)
