from fastapi import Request

from app.services.audit_service import AuditService


def get_audit_service(request: Request) -> AuditService:
    return request.app.state.audit_service
