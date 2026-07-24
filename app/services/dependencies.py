from functools import lru_cache

from app.config import get_settings
from app.services.audit_service import AuditService


@lru_cache
def get_audit_service() -> AuditService:
    return AuditService(get_settings())
