from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_url(value: str) -> str:
    """Normalize a user-entered HTTP(S) URL without issuing a network request."""
    candidate = value.strip()
    if not candidate:
        raise ValueError("URL must not be empty.")
    try:
        initial_scheme = urlsplit(candidate).scheme.lower()
    except ValueError as exc:
        raise ValueError("URL is malformed.") from exc
    if initial_scheme in {"ftp", "file", "javascript", "mailto", "data"}:
        raise ValueError("Only http and https URLs are supported.")
    if "://" not in candidate:
        candidate = f"https://{candidate}"

    try:
        parsed = urlsplit(candidate)
    except ValueError as exc:
        raise ValueError("URL is malformed.") from exc
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Only http and https URLs are supported.")
    try:
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("URL is malformed.") from exc
    if not hostname:
        raise ValueError("URL must include a hostname.")
    if any(character.isspace() for character in candidate):
        raise ValueError("URL must not contain whitespace.")

    return urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path or "/", parsed.query, ""))


class AuditRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    url: str = Field(min_length=1, max_length=2_048)

    @field_validator("url")
    @classmethod
    def validate_and_normalize_url(cls, value: str) -> str:
        return normalize_url(value)


class ParsedPage(BaseModel):
    title: str | None
    meta_description: str | None
    h1_count: int = Field(ge=0)
    images_missing_alt_text: int = Field(ge=0)
    approximate_word_count: int = Field(ge=0)


class AuditResponse(ParsedPage):
    url: str
    http_status: int = Field(ge=100, le=599)
    response_time_ms: float = Field(ge=0)


class HealthResponse(BaseModel):
    status: str
