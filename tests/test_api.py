import asyncio
from uuid import UUID

from fastapi.testclient import TestClient
import httpx

from app.config import Settings
from app.main import app, create_app
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


def test_request_id_header_is_returned_for_successful_requests() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert UUID(request_id)


def test_cors_preflight_returns_200_and_origin_header() -> None:
    cors_app = create_app(Settings(allowed_origins="https://page-pulse-hazel.vercel.app"))

    with TestClient(cors_app) as client:
        response = client.options(
            "/api/v1/audits",
            headers={
                "Origin": "https://page-pulse-hazel.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://page-pulse-hazel.vercel.app"
    assert response.headers["access-control-allow-methods"]
    assert response.headers["X-Request-ID"]


def test_rate_limit_returns_structured_error_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html><head><title>Example</title></head><body><h1>Heading</h1></body></html>",
            request=request,
        )

    async def create_service() -> AuditService:
        service = AuditService(Settings(rate_limit="2/minute", max_response_bytes=1024))
        await service.close()
        service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
        return service

    service = asyncio.run(create_service())
    limited_app = create_app(Settings(rate_limit="2/minute"))
    limited_app.dependency_overrides[get_audit_service] = lambda: service
    try:
        with TestClient(limited_app) as client:
            for _ in range(2):
                success = client.post("/api/v1/audits", json={"url": "https://8.8.8.8/page"})
                assert success.status_code == 200

            limited = client.post("/api/v1/audits", json={"url": "https://8.8.8.8/page"})
    finally:
        limited_app.dependency_overrides.clear()
        asyncio.run(service.close())

    assert limited.status_code == 429
    assert limited.json() == {
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Rate limit exceeded. Please try again later.",
        }
    }
    assert UUID(limited.headers["X-Request-ID"])
