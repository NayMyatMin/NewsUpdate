import asyncio
import logging

import aiohttp

from config.sources import RSSHUB_ROUTES
from config.settings import RSSHUB_BASE_URL
from sources.rss_fetcher import RSSFetcher

logger = logging.getLogger(__name__)

# Fallback public RSSHub instances (tried in order when primary fails)
RSSHUB_FALLBACK_INSTANCES = [
    "https://hub.slarker.me",
    "https://rsshub.qufy.me",
    "https://rsshub.wkfg.me",
    "https://rss.shab.fun",
]


class RSSHubFetcher(RSSFetcher):
    """Fetches news sources via RSSHub with automatic fallback instances."""

    def __init__(self, timeout: int = 30):
        self.routes = RSSHUB_ROUTES
        self.primary_base = RSSHUB_BASE_URL
        self._route_map = {}  # url -> route path

        feeds = []
        for route in self.routes:
            url = f"{self.primary_base}{route['route']}"
            feeds.append({
                "url": url,
                "source": route["source"],
                "lang": route["lang"],
            })
            self._route_map[url] = route["route"]

        super().__init__(feeds=feeds, timeout=timeout)
        logger.info(
            f"RSSHubFetcher initialized with {len(feeds)} routes "
            f"(base: {self.primary_base}, {len(RSSHUB_FALLBACK_INSTANCES)} fallbacks)"
        )

    async def _try_fetch(self, session, url):
        """Try fetching a URL, return (status_code, content) or (error_code, None)."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                if resp.status != 200:
                    return resp.status, None
                return 200, await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return 0, None

    async def _fetch_feed(self, session, feed_info):
        """Try primary instance first, fall back to alternatives on non-200."""
        url = feed_info["url"]
        source = feed_info["source"]
        route_path = self._route_map.get(url)

        # Try primary
        status, content = await self._try_fetch(session, url)
        if status == 200 and content:
            return self._parse_feed(feed_info, content)

        # Only try fallbacks for RSSHub routes
        if route_path is None:
            if status != 200:
                logger.warning(f"[{source}] HTTP {status} for {url}")
            return []

        # Try fallback instances
        for fallback_base in RSSHUB_FALLBACK_INSTANCES:
            fallback_url = f"{fallback_base}{route_path}"
            status, content = await self._try_fetch(session, fallback_url)
            if status == 200 and content:
                logger.info(f"[{source}] Fallback succeeded: {fallback_base}")
                fallback_info = {**feed_info, "url": fallback_url}
                return self._parse_feed(fallback_info, content)

        logger.warning(f"[{source}] All instances failed for {route_path}")
        return []
