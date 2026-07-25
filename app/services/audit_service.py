import asyncio
import ipaddress
import logging
import socket
import ssl
from cachetools import TTLCache
from dataclasses import dataclass
from time import perf_counter
from typing import NoReturn
from urllib.parse import urlsplit

import httpx

from app.config import Settings
from app.errors import AuditError
from app.parsers.html_parser import parse_html
from app.schemas.audit import AuditResponse

logger = logging.getLogger(__name__)
_REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}
_HTML_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}


@dataclass(frozen=True)
class FetchedPage:
    """The bounded HTML response required to produce an audit report."""

    url: str
    http_status: int
    html: str
    response_time_ms: float


class AuditService:
    """Fetch public HTML pages and turn them into Page Pulse reports."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.fetch_timeout_seconds),
            follow_redirects=False,
            headers={"User-Agent": settings.user_agent},
        )
        self._cache: TTLCache[str, AuditResponse] = TTLCache(maxsize=1_024, ttl=settings.cache_ttl_seconds)
        self._cache_lock = asyncio.Lock()
        self._fetch_semaphore = asyncio.Semaphore(settings.max_concurrent_requests)

    async def close(self) -> None:
        """Release pooled HTTP connections during application shutdown."""
        await self._client.aclose()

    async def audit(self, url: str) -> AuditResponse:
        cached_report = await self._get_cached_report(url)
        if cached_report is not None:
            return cached_report

        async with self._fetch_semaphore:
            fetched_page = await self._fetch(url)
        parsed_page = parse_html(fetched_page.html)
        report = AuditResponse(
            url=fetched_page.url,
            http_status=fetched_page.http_status,
            response_time_ms=fetched_page.response_time_ms,
            **parsed_page.model_dump(),
        )
        await self._set_cached_report(url, report)
        return report

    async def _get_cached_report(self, url: str) -> AuditResponse | None:
        async with self._cache_lock:
            cached_report = self._cache.get(url)
            if cached_report is None:
                return None
            return cached_report.model_copy(deep=True)

    async def _set_cached_report(self, url: str, report: AuditResponse) -> None:
        async with self._cache_lock:
            self._cache[url] = report.model_copy(deep=True)

    async def _fetch(self, initial_url: str) -> FetchedPage:
        current_url = initial_url
        started_at = perf_counter()

        for redirect_count in range(self._settings.max_redirects + 1):
            await _ensure_public_target(current_url)
            try:
                async with self._client.stream("GET", current_url) as response:
                    if response.status_code in _REDIRECT_STATUS_CODES:
                        current_url = self._next_redirect_url(response, redirect_count)
                        continue

                    self._ensure_html(response)
                    body = await self._read_bounded_body(response)
                    elapsed_ms = round((perf_counter() - started_at) * 1_000, 2)
                    encoding = response.encoding or "utf-8"
                    return FetchedPage(
                        url=str(response.url),
                        http_status=response.status_code,
                        html=body.decode(encoding, errors="replace"),
                        response_time_ms=elapsed_ms,
                    )
            except AuditError:
                raise
            except httpx.TimeoutException as exc:
                self._raise_fetch_error(504, "FETCH_TIMEOUT", "The page took too long to respond.", exc)
            except httpx.ConnectError as exc:
                self._raise_connection_error(exc)
            except httpx.RequestError as exc:
                self._raise_fetch_error(502, "FETCH_FAILED", "The page could not be fetched.", exc)

        raise AuditError(
            status_code=502,
            code="REDIRECT_FAILED",
            message="The page redirected too many times.",
        )

    def _next_redirect_url(self, response: httpx.Response, redirect_count: int) -> str:
        if redirect_count >= self._settings.max_redirects:
            raise AuditError(
                status_code=502,
                code="REDIRECT_FAILED",
                message="The page redirected too many times.",
            )
        location = response.headers.get("location")
        if not location:
            raise AuditError(
                status_code=502,
                code="REDIRECT_FAILED",
                message="The page returned a redirect without a destination.",
            )
        return str(response.url.join(location))

    async def _read_bounded_body(self, response: httpx.Response) -> bytes:
        content_length = response.headers.get("content-length")
        if content_length is not None and content_length.isdigit() and int(content_length) > self._settings.max_response_bytes:
            raise AuditError(
                status_code=413,
                code="RESPONSE_TOO_LARGE",
                message="The HTML page is too large to analyse.",
            )

        body = bytearray()
        async for chunk in response.aiter_bytes():
            body.extend(chunk)
            if len(body) > self._settings.max_response_bytes:
                raise AuditError(
                    status_code=413,
                    code="RESPONSE_TOO_LARGE",
                    message="The HTML page is too large to analyse.",
                )
        return bytes(body)

    @staticmethod
    def _ensure_html(response: httpx.Response) -> None:
        media_type = response.headers.get("content-type", "").split(";", maxsplit=1)[0].strip().lower()
        if media_type not in _HTML_CONTENT_TYPES:
            raise AuditError(
                status_code=422,
                code="NON_HTML_RESPONSE",
                message="The URL returned content that is not an HTML page.",
            )

    @staticmethod
    def _raise_connection_error(exc: httpx.ConnectError) -> NoReturn:
        if _has_cause(exc, ssl.SSLError):
            AuditService._raise_fetch_error(502, "SSL_FAILED", "A secure connection to the page could not be established.", exc)
        if _has_cause(exc, socket.gaierror):
            AuditService._raise_fetch_error(502, "DNS_FAILED", "The page hostname could not be resolved.", exc)
        AuditService._raise_fetch_error(502, "CONNECTION_FAILED", "A connection to the page could not be established.", exc)

    @staticmethod
    def _raise_fetch_error(status_code: int, code: str, message: str, exc: Exception) -> NoReturn:
        logger.info("Page fetch failed with code=%s.", code)
        raise AuditError(status_code=status_code, code=code, message=message) from exc


async def _ensure_public_target(url: str) -> None:
    """Reject local and private destinations before each request, including redirects."""
    parsed = urlsplit(url)
    hostname = parsed.hostname
    if parsed.scheme not in {"http", "https"}:
        raise AuditError(
            status_code=400,
            code="BLOCKED_URL",
            message="Only http and https URLs are supported.",
        )
    if not hostname:
        raise AuditError(status_code=400, code="INVALID_URL", message="URL must include a hostname.")

    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        literal_ip = None

    if literal_ip is not None:
        _ensure_global_ip(literal_ip)
        return

    try:
        addresses = await asyncio.get_running_loop().getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise AuditError(
            status_code=502,
            code="DNS_FAILED",
            message="The page hostname could not be resolved.",
        ) from exc

    for address in addresses:
        _ensure_global_ip(ipaddress.ip_address(address[4][0]))


def _ensure_global_ip(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if not address.is_global:
        raise AuditError(
            status_code=400,
            code="BLOCKED_URL",
            message="URLs pointing to private or local networks are not supported.",
        )


def _has_cause(error: BaseException, cause_type: type[BaseException]) -> bool:
    """Check an exception chain without exposing low-level errors to clients."""
    current: BaseException | None = error
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, cause_type):
            return True
        current = current.__cause__ or current.__context__
    return False
