import asyncio
from collections.abc import Callable

import httpx
import pytest

from app.config import Settings
from app.errors import AuditError
from app.services.audit_service import AuditService

MockHandler = Callable[[httpx.Request], httpx.Response]


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


def test_audit_uses_cached_result_for_repeated_url_requests() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        handler.call_count += 1
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html><head><title>Cached page</title></head><body><h1>Hello</h1></body></html>",
            request=request,
        )

    handler.call_count = 0

    async def run() -> None:
        service = await _create_service(handler, Settings(max_response_bytes=1024, cache_ttl_seconds=300))
        try:
            first = await service.audit("https://8.8.8.8/page")
            second = await service.audit("https://8.8.8.8/page")
        finally:
            await service.close()

        assert first.model_dump() == second.model_dump()
        assert handler.call_count == 1

    asyncio.run(run())


def test_audit_refreshes_cache_after_ttl_expiry() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        handler.call_count += 1
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html><head><title>Expiring page</title></head><body><h1>Hello</h1></body></html>",
            request=request,
        )

    handler.call_count = 0

    async def run() -> None:
        service = await _create_service(handler, Settings(max_response_bytes=1024, cache_ttl_seconds=1))
        try:
            await service.audit("https://8.8.8.8/page")
            await asyncio.sleep(1.1)
            await service.audit("https://8.8.8.8/page")
        finally:
            await service.close()

        assert handler.call_count == 2

    asyncio.run(run())


def test_audit_respects_configured_concurrency_limit() -> None:
    active_fetches = 0
    max_active_fetches = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal active_fetches, max_active_fetches
        active_fetches += 1
        max_active_fetches = max(max_active_fetches, active_fetches)
        await asyncio.sleep(0.05)
        active_fetches -= 1
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html><head><title>Concurrent page</title></head><body><h1>Hello</h1></body></html>",
            request=request,
        )

    async def run() -> None:
        service = await _create_service(handler, Settings(max_response_bytes=1024, max_concurrent_requests=1))
        try:
            await asyncio.gather(
                service.audit("https://8.8.8.8/page-one"),
                service.audit("https://1.1.1.1/page-two"),
            )
        finally:
            await service.close()

        assert max_active_fetches == 1

    asyncio.run(run())


async def _create_service(handler: MockHandler, settings: Settings) -> AuditService:
    service = AuditService(settings)
    await service.close()
    service._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
    return service
