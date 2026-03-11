import asyncio
import logging
from datetime import datetime, timedelta, timezone

import aiohttp
import feedparser

from models.article import Article
from config.topics import match_topics
from sources.base import BaseFetcher

logger = logging.getLogger(__name__)


class RSSFetcher(BaseFetcher):
    """Fetches and parses RSS/Atom feeds."""

    def __init__(self, feeds: list[dict], timeout: int = 30):
        """
        Args:
            feeds: List of dicts with 'url', 'source', 'lang' keys
            timeout: Request timeout in seconds
        """
        self.feeds = feeds
        self.timeout = timeout

    async def _fetch_feed(
        self, session: aiohttp.ClientSession, feed_info: dict
    ) -> list[Article]:
        """Fetch and parse a single RSS feed."""
        url = feed_info["url"]
        source = feed_info["source"]
        lang = feed_info["lang"]
        articles = []

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                if resp.status != 200:
                    logger.warning(f"[{source}] HTTP {resp.status} for {url}")
                    return []
                content = await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"[{source}] Fetch error: {e}")
            return []

        parsed = feedparser.parse(content)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=28)  # Slight buffer

        for entry in parsed.entries:
            # Parse published date
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    pass
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                try:
                    published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    pass

            # Filter to last ~24 hours (skip if no date - include it)
            if published and published < cutoff:
                continue

            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue

            # Extract snippet from summary/description
            snippet = ""
            if hasattr(entry, "summary"):
                snippet = entry.summary[:500]
            elif hasattr(entry, "description"):
                snippet = entry.description[:500]

            # Strip HTML tags from snippet
            import re
            snippet = re.sub(r"<[^>]+>", " ", snippet).strip()
            snippet = re.sub(r"\s+", " ", snippet)[:500]

            # Match topics
            text_for_matching = f"{title} {snippet}"
            topics = match_topics(text_for_matching)

            articles.append(Article(
                title=title,
                url=link,
                source=source,
                language=lang,
                published=published,
                snippet=snippet,
                topic_matches=topics,
            ))

        logger.info(f"[{source}] Fetched {len(articles)} articles from last 24h")
        return articles

    async def fetch(self) -> list[Article]:
        """Fetch all configured RSS feeds in parallel."""
        all_articles = []
        async with aiohttp.ClientSession(
            headers={"User-Agent": "NewsUpdateBot/1.0"}
        ) as session:
            tasks = [self._fetch_feed(session, feed) for feed in self.feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Feed fetch exception: {result}")
        return all_articles
