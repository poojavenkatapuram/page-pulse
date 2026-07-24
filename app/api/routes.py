from fastapi import APIRouter, Depends, status

from app.schemas.audit import AuditRequest, AuditResponse, HealthResponse
from app.schemas.error import ErrorResponse
from app.services.audit_service import AuditService
from app.services.dependencies import get_audit_service

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
        502: {"model": ErrorResponse, "description": "The target could not be reached."},
        504: {"model": ErrorResponse, "description": "The target timed out."},
    },
    tags=["audits"],
)
async def create_audit(
    payload: AuditRequest,
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditResponse:
    """Fetch and analyse one HTML page."""
    return await audit_service.audit(payload.url)
