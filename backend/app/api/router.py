"""Route composition. Do not put business rules here."""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.modules.auth.router import router as auth_router

router = APIRouter()

router.include_router(health_router, prefix="/api/v1")
router.include_router(auth_router, prefix="/api/v1")