from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app


def test_request_id_header_is_returned_for_validation_errors() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/audits", json={"url": "ftp://example.com"})

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert UUID(request_id)
