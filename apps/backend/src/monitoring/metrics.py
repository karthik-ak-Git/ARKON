from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import logging

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._request_count = 0
        self._error_count = 0
        self._total_response_time = 0.0

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        self._request_count += 1

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            self._error_count += 1
            logger.error("Request failed", exc_info=exc)
            raise
        finally:
            duration = time.time() - start_time
            self._total_response_time += duration
            logger.info(
                "Request metrics",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": getattr(response, "status_code", None),
                    "duration_ms": round(duration * 1000, 2),
                    "total_requests": self._request_count,
                    "total_errors": self._error_count,
                    "avg_response_time_ms": round(
                        (self._total_response_time / self._request_count) * 1000, 2
                    ),
                },
            )