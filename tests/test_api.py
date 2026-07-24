import asyncio

from fastapi.testclient import TestClient
import httpx

from app.config import Settings
from app.main import app
from app.services.audit_service import AuditService
from app.services.dependencies import get_audit_service


def test_health_endpoint_returns_typed_response() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_audit_request_uses_standard_error_envelope() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/audits", json={"url": "ftp://example.com"})

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "INVALID_REQUEST",
            "message": "Provide a valid URL in the request body.",
        }
    }


def test_successful_audit_returns_complete_response_schema() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html><head><title>Example</title><meta name='description' content='Sample'></head><body><h1>Heading</h1></body></html>",
            request=request,
        )

    async def create_service() -> AuditService:
        service = AuditService(Settings(max_response_bytes=1024))
        await service.close()
        service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
        return service

    service = asyncio.run(create_service())
    app.dependency_overrides[get_audit_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/audits", json={"url": "https://8.8.8.8/page"})
    finally:
        app.dependency_overrides.clear()
        asyncio.run(service.close())

    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://8.8.8.8/page"
    assert data["http_status"] == 200
    assert isinstance(data["response_time_ms"], float)
    assert data["title"] == "Example"
    assert data["meta_description"] == "Sample"
    assert data["h1_count"] == 1
    assert data["images_missing_alt_text"] == 0
    assert data["approximate_word_count"] == 1
