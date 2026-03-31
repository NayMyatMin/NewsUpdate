"""
Async full-text content fetcher for L2 candidate articles.

Fetches actual web page content for articles that survived L1 screening,
extracts readable text from HTML, and returns it for use in L2 deep analysis.
Falls back gracefully to the original snippet on any failure.
"""

import asyncio
import logging
import re

import aiohttp
from bs4 import BeautifulSoup

from config.settings import MAX_FULLTEXT_LENGTH
from models.article import Article

logger = logging.getLogger(__name__)

# Reasonable browser User-Agent to avoid being blocked
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Tags whose content is not useful article text
_STRIP_TAGS = {
    "script", "style", "nav", "header", "footer", "aside",
    "form", "button", "noscript", "svg", "iframe",
}


def _extract_text_from_html(html: str, max_length: int = MAX_FULLTEXT_LENGTH) -> str:
    """
    Extract readable article text from raw HTML.

    Uses BeautifulSoup to strip non-content tags, then extracts text.
    Tries to find a <main> or <article> element first for better signal.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove non-content tags entirely
    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()

    # Try to find the main article content area
    content_node = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=re.compile(r"(article|content|post|entry)", re.I))
        or soup.find("div", id=re.compile(r"(article|content|post|entry)", re.I))
    )

    if content_node is None:
        content_node = soup.body or soup

    # Get text, collapse whitespace
    raw_text = content_node.get_text(separator="\n", strip=True)
    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", raw_text)
    # Collapse runs of spaces within lines
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text[:max_length].strip()


async def _fetch_one(
    session: aiohttp.ClientSession,
    url: str,
    semaphore: asyncio.Semaphore,
    timeout: float,
    max_length: int,
) -> tuple[str, str | None]:
    """
    Fetch and extract text from a single URL.

    Returns (url, extracted_text) on success or (url, None) on failure.
    """
    async with semaphore:
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=True,
                ssl=False,
            ) as response:
                if response.status != 200:
                    logger.debug(f"Content fetch HTTP {response.status} for {url}")
                    return (url, None)

                # Only process HTML responses
                content_type = response.headers.get("Content-Type", "")
                if "html" not in content_type.lower() and "text" not in content_type.lower():
                    logger.debug(f"Non-HTML content type '{content_type}' for {url}")
                    return (url, None)

                html = await response.text(errors="replace")
                text = _extract_text_from_html(html, max_length=max_length)

                if len(text) < 100:
                    # Too little text extracted, not useful
                    logger.debug(f"Extracted text too short ({len(text)} chars) for {url}")
                    return (url, None)

                return (url, text)

        except asyncio.TimeoutError:
            logger.debug(f"Content fetch timeout for {url}")
            return (url, None)
        except Exception as e:
            logger.debug(f"Content fetch error for {url}: {e}")
            return (url, None)


async def fetch_full_text(
    articles: list[Article],
    timeout_per_article: float = 10.0,
    max_concurrent: int = 5,
    max_length: int = MAX_FULLTEXT_LENGTH,
) -> dict[str, str]:
    """
    Fetch full article text for a list of articles in parallel.

    Args:
        articles: List of Article objects to fetch content for.
        timeout_per_article: HTTP timeout in seconds per article.
        max_concurrent: Maximum number of concurrent requests.
        max_length: Maximum character length of extracted text.

    Returns:
        Dict mapping URL -> extracted full text. Only includes URLs where
        fetching and extraction succeeded. Missing URLs should fall back
        to their original snippet.
    """
    if not articles:
        return {}

    semaphore = asyncio.Semaphore(max_concurrent)
    headers = {"User-Agent": _USER_AGENT}

    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [
            _fetch_one(session, article.url, semaphore, timeout_per_article, max_length)
            for article in articles
        ]
        results = await asyncio.gather(*tasks)

    # Build result dict, skipping failures
    full_texts = {}
    for url, text in results:
        if text is not None:
            full_texts[url] = text

    return full_texts
