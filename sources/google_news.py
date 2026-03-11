import logging
from urllib.parse import quote

from config.sources import GOOGLE_NEWS_QUERIES
from sources.rss_fetcher import RSSFetcher

logger = logging.getLogger(__name__)


def build_google_news_url(query: str, lang: str = "en") -> str:
    """Build a Google News RSS search URL."""
    encoded_query = quote(query)
    if lang == "zh":
        return (
            f"https://news.google.com/rss/search?"
            f"q={encoded_query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        )
    return (
        f"https://news.google.com/rss/search?"
        f"q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    )


class GoogleNewsFetcher(RSSFetcher):
    """Fetches news from Google News RSS search."""

    def __init__(self, timeout: int = 30):
        feeds = []
        for q in GOOGLE_NEWS_QUERIES:
            url = build_google_news_url(q["query"], q["lang"])
            source_name = f"Google News ({q['lang'].upper()})"
            feeds.append({
                "url": url,
                "source": source_name,
                "lang": q["lang"],
            })
        super().__init__(feeds=feeds, timeout=timeout)
        logger.info(f"GoogleNewsFetcher initialized with {len(feeds)} queries")
