import asyncio
import socket
import ssl
from collections.abc import Callable

import httpx
import pytest

from app.config import Settings
from app.errors import AuditError
from app.services.audit_service import AuditService

MockHandler = Callable[[httpx.Request], httpx.Response]


def test_timeout_is_mapped_to_gateway_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    error = _run_audit(handler)

    assert error.status_code == 504
    assert error.code == "FETCH_TIMEOUT"


def test_dns_failure_is_mapped_to_bad_gateway() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        try:
            raise socket.gaierror("hostname not found")
        except socket.gaierror as cause:
            raise httpx.ConnectError("connection failed", request=request) from cause

    error = _run_audit(handler)

    assert error.status_code == 502
    assert error.code == "DNS_FAILED"


def test_ssl_failure_is_mapped_to_bad_gateway() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        try:
            raise ssl.SSLError("certificate verification failed")
        except ssl.SSLError as cause:
            raise httpx.ConnectError("connection failed", request=request) from cause

    error = _run_audit(handler)

    assert error.status_code == 502
    assert error.code == "SSL_FAILED"


def test_non_html_response_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "application/json"}, content=b"{}", request=request)

    error = _run_audit(handler)

    assert error.status_code == 422
    assert error.code == "NON_HTML_RESPONSE"


def test_oversized_response_is_rejected_before_parsing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html", "content-length": "1025"},
            content=b"<html></html>",
            request=request,
        )

    error = _run_audit(handler)

    assert error.status_code == 413
    assert error.code == "RESPONSE_TOO_LARGE"


def _run_audit(handler: MockHandler) -> AuditError:
    async def run() -> AuditError:
        service = AuditService(Settings(max_response_bytes=1024))
        await service.close()
        service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
        try:
            with pytest.raises(AuditError) as error:
                await service.audit("https://8.8.8.8/page")
            return error.value
        finally:
            await service.close()

    return asyncio.run(run())
