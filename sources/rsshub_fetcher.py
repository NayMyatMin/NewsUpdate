import logging

from config.sources import RSSHUB_ROUTES
from config.settings import RSSHUB_BASE_URL
from sources.rss_fetcher import RSSFetcher

logger = logging.getLogger(__name__)


class RSSHubFetcher(RSSFetcher):
    """Fetches Chinese news sources via RSSHub."""

    def __init__(self, timeout: int = 30):
        feeds = []
        for route in RSSHUB_ROUTES:
            url = f"{RSSHUB_BASE_URL}{route['route']}"
            feeds.append({
                "url": url,
                "source": route["source"],
                "lang": route["lang"],
            })
        super().__init__(feeds=feeds, timeout=timeout)
        logger.info(
            f"RSSHubFetcher initialized with {len(feeds)} routes "
            f"(base: {RSSHUB_BASE_URL})"
        )
