import pytest

from app.schemas.audit import normalize_url


def test_normalize_url_adds_https_scheme() -> None:
    assert normalize_url("example.com/articles") == "https://example.com/articles"


@pytest.mark.parametrize("url", ["", "ftp://example.com", "mailto:test@example.com", "https://[bad"])
def test_normalize_url_rejects_invalid_or_unsupported_urls(url: str) -> None:
    with pytest.raises(ValueError):
        normalize_url(url)
