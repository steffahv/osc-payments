"""ASGI entry point. Phase B exposes infrastructure checks only."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.core.config import get_settings
from app.db.session import get_engine
from app.core.origin_security import OriginSecurityMiddleware
from app.api.health import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.master_data.router import router as master_data_router
from app.modules.receipts.router import router as receipts_router
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()


def create_app() -> FastAPI:
    settings = get_settings()
    development = settings.app_env != "production"
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/api/docs" if development else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if development else None,
        lifespan=lifespan,
    )
    app.add_middleware(OriginSecurityMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(master_data_router, prefix="/api/v1")
    app.include_router(receipts_router, prefix="/api/v1")
    return app


app = create_app()
