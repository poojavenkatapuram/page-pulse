import re

from bs4 import BeautifulSoup
from bs4.element import Tag

from app.errors import AuditError
from app.schemas.audit import ParsedPage

_WHITESPACE = re.compile(r"\s+")
_WORD = re.compile(r"\b\w+\b", flags=re.UNICODE)


def parse_html(html: str) -> ParsedPage:
    """Extract the required report data from an HTML document.

    Images with an absent or whitespace-only ``alt`` attribute are reported as
    missing alt text. An explicit ``alt=\"\"`` is treated as decorative.
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        title = _text_or_none(soup.title)
        description = _meta_description(soup)
        h1_count = len(soup.find_all("h1"))
        images_missing_alt_text = sum(_is_missing_alt_text(image) for image in soup.find_all("img"))

        for element in soup(["head", "script", "style", "noscript", "template"]):
            element.decompose()
        for element in soup.select("[hidden], [aria-hidden='true']"):
            element.decompose()
        visible_text = soup.get_text(" ", strip=True)
        approximate_word_count = len(_WORD.findall(visible_text))

        return ParsedPage(
            title=title,
            meta_description=description,
            h1_count=h1_count,
            images_missing_alt_text=images_missing_alt_text,
            approximate_word_count=approximate_word_count,
        )
    except AuditError:
        raise
    except Exception as exc:
        raise AuditError(
            status_code=422,
            code="PARSE_FAILED",
            message="The HTML page could not be parsed.",
        ) from exc


def _text_or_none(element: Tag | None) -> str | None:
    if element is None:
        return None
    text = _WHITESPACE.sub(" ", element.get_text(" ", strip=True)).strip()
    return text or None


def _meta_description(soup: BeautifulSoup) -> str | None:
    for tag in soup.find_all("meta"):
        name = tag.get("name")
        if isinstance(name, str) and name.lower() == "description":
            content = tag.get("content")
            if isinstance(content, str):
                return _WHITESPACE.sub(" ", content).strip() or None
    return None


def _is_missing_alt_text(image: Tag) -> bool:
    """Respect empty alt text as the HTML convention for decorative images."""
    alt_text = image.get("alt")
    return alt_text is None or (isinstance(alt_text, str) and alt_text != "" and not alt_text.strip())
