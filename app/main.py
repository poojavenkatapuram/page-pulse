import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import get_router
from app.config import Settings, get_settings
from app.errors import AuditError
from app.schemas.error import ErrorDetail, ErrorResponse
from app.services.audit_service import AuditService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    limiter = Limiter(key_func=get_remote_address, default_limits=[])

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Manage shared outbound HTTP resources for the application lifetime."""
        app.state.audit_service = AuditService(resolved_settings)
        try:
            yield
        finally:
            await app.state.audit_service.close()

    app = FastAPI(title=resolved_settings.app_name, version="1.0.0", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.limiter = limiter

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = str(uuid4())
        request_start = perf_counter()
        request.state.request_id = request_id
        request.state.client_ip = _get_client_ip(request)
        request.state.audit_url = None

        if request.method == "OPTIONS":
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        response_time_ms = round((perf_counter() - request_start) * 1_000, 2)
        logger.info(
            "request_id=%s client_ip=%s method=%s path=%s audit_url=%s status_code=%s response_time_ms=%.2f",
            request_id,
            request.state.client_ip,
            request.method,
            request.url.path,
            getattr(request.state, "audit_url", None),
            response.status_code,
            response_time_ms,
        )
        return response

    @app.exception_handler(AuditError)
    async def handle_audit_error(_: Request, exc: AuditError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=ErrorDetail(code=exc.code, message=exc.message)).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        request.state.audit_url = _extract_audit_url(exc.body)
        logger.info("Rejected invalid API request with %d validation error(s).", len(exc.errors()))
        response = ErrorResponse(
            error=ErrorDetail(code="INVALID_REQUEST", message="Provide a valid URL in the request body.")
        )
        return JSONResponse(status_code=400, content=response.model_dump())

    @app.exception_handler(RateLimitExceeded)
    async def handle_rate_limit_exceeded(request: Request, _: RateLimitExceeded) -> JSONResponse:
        response = JSONResponse(
            status_code=429,
            content=ErrorResponse(
                error=ErrorDetail(code="RATE_LIMIT_EXCEEDED", message="Rate limit exceeded. Please try again later.")
            ).model_dump(),
        )
        response.headers["X-Request-ID"] = getattr(request.state, "request_id", "")
        return response

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request.state.audit_url = getattr(request.state, "audit_url", None)
        logger.exception("Unhandled application error", exc_info=exc)
        response = ErrorResponse(
            error=ErrorDetail(code="INTERNAL_ERROR", message="An unexpected server error occurred.")
        )
        return JSONResponse(status_code=500, content=response.model_dump())

    app.include_router(get_router(resolved_settings.rate_limit, limiter))
    return app


def _extract_audit_url(body: object) -> str | None:
    if isinstance(body, dict):
        value = body.get("url")
        if isinstance(value, str):
            return value
    if isinstance(body, str):
        try:
            parsed_body = json.loads(body)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed_body, dict):
            value = parsed_body.get("url")
            if isinstance(value, str):
                return value
    return None


def _get_client_ip(request: Request) -> str:
    if request.client is None:
        return "unknown"
    return request.client.host


app = create_app()
