"""
WeChat public account article scraper via Sogou WeChat Search.
Note: This is fragile and may break if Sogou changes their page structure.
Falls back gracefully — never blocks the pipeline.
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from urllib.parse import quote

import aiohttp
from bs4 import BeautifulSoup

from config.sources import WECHAT_SEARCH_QUERIES
from config.topics import match_topics
from models.article import Article
from sources.base import BaseFetcher

logger = logging.getLogger(__name__)

SOGOU_WECHAT_URL = "https://weixin.sogou.com/weixin"

# Rotate user agents to reduce blocking
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class WeChatScraper(BaseFetcher):
    """Scrapes WeChat public account articles via Sogou WeChat Search."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.queries = WECHAT_SEARCH_QUERIES

    async def _search_query(
        self, session: aiohttp.ClientSession, query: str, ua_index: int
    ) -> list[Article]:
        """Search Sogou WeChat for a single query."""
        articles = []
        params = {
            "type": "2",  # Article search
            "query": query,
            "ie": "utf8",
            "s_from": "input",
            "_sug_": "n",
            "_sug_type_": "",
        }
        headers = {
            "User-Agent": USER_AGENTS[ua_index % len(USER_AGENTS)],
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://weixin.sogou.com/",
        }

        try:
            async with session.get(
                SOGOU_WECHAT_URL,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                allow_redirects=True,
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"[WeChat/{query}] HTTP {resp.status}")
                    return []
                html = await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"[WeChat/{query}] Fetch error: {e}")
            return []

        soup = BeautifulSoup(html, "lxml")

        # Sogou WeChat search results are in <div class="txt-box">
        for item in soup.select("div.txt-box"):
            try:
                # Title and link
                title_tag = item.select_one("h3 a")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                url = title_tag.get("href", "")
                if not title or not url:
                    continue

                # Make URL absolute
                if url.startswith("/"):
                    url = f"https://weixin.sogou.com{url}"

                # Snippet
                snippet_tag = item.select_one("p.txt-info")
                snippet = snippet_tag.get_text(strip=True)[:500] if snippet_tag else ""

                # Account name
                account_tag = item.select_one("div.s-p a")
                account = account_tag.get_text(strip=True) if account_tag else "WeChat"

                # Date extraction — try multiple strategies
                published = None

                # Strategy 1: timestamp in nearby script tag (timeConvert pattern)
                try:
                    script = item.find_next("script")
                    if script and script.string:
                        ts_match = re.search(r"timeConvert\('(\d+)'\)", script.string)
                        if ts_match:
                            published = datetime.fromtimestamp(int(ts_match.group(1)), tz=timezone.utc)
                except (ValueError, OSError):
                    pass

                # Strategy 2: data-lastmodified or data-t attribute on any element
                if not published:
                    for attr in ("data-lastmodified", "data-t", "data-time"):
                        tag_with_ts = item.find(attrs={attr: True})
                        if tag_with_ts:
                            try:
                                ts = int(tag_with_ts[attr])
                                published = datetime.fromtimestamp(ts, tz=timezone.utc)
                                break
                            except (ValueError, OSError):
                                continue

                # Strategy 3: any 10-digit timestamp in the item's scripts
                if not published:
                    for script in item.find_all("script"):
                        if script.string:
                            ts_match = re.search(r"\b(\d{10})\b", script.string)
                            if ts_match:
                                try:
                                    published = datetime.fromtimestamp(int(ts_match.group(1)), tz=timezone.utc)
                                    break
                                except (ValueError, OSError):
                                    continue

                # Strategy 4: fall back to current time (article appeared in search = recent)
                if not published:
                    published = datetime.now(timezone.utc)

                text = f"{title} {snippet}"
                topics = match_topics(text)

                articles.append(Article(
                    title=title,
                    url=url,
                    source=f"WeChat ({account})",
                    language="zh",
                    published=published,
                    snippet=snippet,
                    topic_matches=topics,
                ))
            except Exception as e:
                logger.debug(f"[WeChat/{query}] Parse error for item: {e}")
                continue

        logger.info(f"[WeChat/{query}] Scraped {len(articles)} articles")
        return articles

    async def fetch(self) -> list[Article]:
        """Fetch from all WeChat search queries sequentially with delays."""
        all_articles = []

        async with aiohttp.ClientSession() as session:
            for i, query in enumerate(self.queries):
                results = await self._search_query(session, query, i)
                all_articles.extend(results)
                # Small delay between requests to avoid rate limiting
                if i < len(self.queries) - 1:
                    await asyncio.sleep(2)

        logger.info(f"WeChat total: {len(all_articles)} articles from {len(self.queries)} queries")
        return all_articles
