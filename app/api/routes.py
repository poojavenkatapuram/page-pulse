from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter

from app.schemas.audit import AuditRequest, AuditResponse, HealthResponse
from app.schemas.error import ErrorResponse
from app.services.audit_service import AuditService
from app.services.dependencies import get_audit_service


def get_router(rate_limit: str, limiter: Limiter) -> APIRouter:
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse, tags=["health"])
    async def health_check() -> HealthResponse:
        """Return a lightweight readiness response for hosting platforms."""
        return HealthResponse(status="ok")

    @router.post(
        "/api/v1/audits",
        response_model=AuditResponse,
        status_code=status.HTTP_200_OK,
        responses={
            400: {"model": ErrorResponse, "description": "Invalid request or blocked URL."},
            413: {"model": ErrorResponse, "description": "Response body is too large to analyse."},
            422: {"model": ErrorResponse, "description": "The target is not processable HTML."},
            429: {"model": ErrorResponse, "description": "Too many requests from this client."},
            502: {"model": ErrorResponse, "description": "The target could not be reached."},
            504: {"model": ErrorResponse, "description": "The target timed out."},
        },
        tags=["audits"],
    )
    @limiter.limit(rate_limit)
    async def create_audit(
        request: Request,
        payload: AuditRequest,
        audit_service: AuditService = Depends(get_audit_service),
    ) -> AuditResponse:
        """Fetch and analyse one HTML page."""
        request.state.audit_url = payload.url
        return await audit_service.audit(payload.url)

    return router
