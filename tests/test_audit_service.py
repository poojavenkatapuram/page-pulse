import asyncio

import httpx
import pytest

from app.config import Settings
from app.errors import AuditError
from app.services.audit_service import AuditService


def test_audit_follows_safe_redirect_and_builds_report() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/start":
            return httpx.Response(302, headers={"location": "/final"}, request=request)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=b"<html><head><title>Final page</title></head><body><h1>Hello</h1>Visible text</body></html>",
            request=request,
        )

    async def run() -> None:
        service = AuditService(Settings(max_response_bytes=1024))
        await service.close()
        service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
        try:
            report = await service.audit("https://8.8.8.8/start")
        finally:
            await service.close()

        assert report.url == "https://8.8.8.8/final"
        assert report.http_status == 200
        assert report.title == "Final page"
        assert report.h1_count == 1

    asyncio.run(run())


def test_audit_blocks_private_network_targets() -> None:
    async def run() -> None:
        service = AuditService(Settings())
        try:
            with pytest.raises(AuditError, match="private or local") as error:
                await service.audit("http://127.0.0.1/internal")
            assert error.value.status_code == 400
            assert error.value.code == "BLOCKED_URL"
        finally:
            await service.close()

    asyncio.run(run())
