import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import get_settings
from app.errors import AuditError
from app.schemas.error import ErrorDetail, ErrorResponse
from app.services.dependencies import get_audit_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage shared outbound HTTP resources for the application lifetime."""
    try:
        yield
    finally:
        await get_audit_service().close()
        get_audit_service.cache_clear()

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(AuditError)
async def handle_audit_error(_: Request, exc: AuditError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=ErrorDetail(code=exc.code, message=exc.message)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    logger.info("Rejected invalid API request with %d validation error(s).", len(exc.errors()))
    response = ErrorResponse(
        error=ErrorDetail(code="INVALID_REQUEST", message="Provide a valid URL in the request body.")
    )
    return JSONResponse(status_code=400, content=response.model_dump())


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error", exc_info=exc)
    response = ErrorResponse(
        error=ErrorDetail(code="INTERNAL_ERROR", message="An unexpected server error occurred.")
    )
    return JSONResponse(status_code=500, content=response.model_dump())


app.include_router(router)
