"""
Middleware de logging des requêtes HTTP — SEINENTAI4US
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("seinentai4us.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log chaque requête avec son temps de réponse et son statut."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}"
            f" → {response.status_code} ({duration_ms:.1f}ms)"
            f" | client={request.client.host if request.client else 'unknown'}"
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
        return response
