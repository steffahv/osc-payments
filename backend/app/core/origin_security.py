"""Protect cookie-authenticated write requests from cross-site requests."""

from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings


class OriginSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            allowed_origin = get_settings().frontend_origin.rstrip("/")

            # Require an exact match, not a substring or suffix.
            if origin != allowed_origin:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Untrusted request origin"},
                )

        return await call_next(request)