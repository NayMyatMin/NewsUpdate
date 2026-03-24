"""
WeChat public account article scraper via Sogou WeChat Search.
Note: This is fragile and may break if Sogou changes their page structure.
Falls back gracefully — never blocks the pipeline.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone

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

    def __init__(self, timeout: int = 15, max_age_days: int = 5, max_pages: int = 2):
        self.timeout = timeout
        self.max_age_days = max_age_days
        self.max_pages = max_pages
        self.queries = WECHAT_SEARCH_QUERIES

    def _build_headers(self, ua_index: int) -> dict:
        return {
            "User-Agent": USER_AGENTS[ua_index % len(USER_AGENTS)],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://weixin.sogou.com/",
            "Connection": "keep-alive",
        }

    def _is_antibot_page(self, html: str, final_url: str) -> bool:
        text = html.lower()
        signals = [
            "antispider",
            "请输入验证码",
            "访问过于频繁",
            "异常访问",
            "security.sogou.com",
        ]
        return any(s.lower() in text for s in signals) or "antispider" in final_url.lower()

    def _extract_timestamp(self, item) -> datetime | None:
        """
        Try to extract published timestamp from scripts inside the result item.
        Common patterns include:
        - timeConvert('1710230400')
        - timeConvert("1710230400")
        """
        scripts = item.find_all("script")
        for script in scripts:
            script_text = script.string or script.get_text() or ""
            patterns = [
                r"timeConvert\('(\d+)'\)",
                r'timeConvert\("(\d+)"\)',
                r"(\d{10})",
            ]
            for pattern in patterns:
                m = re.search(pattern, script_text)
                if not m:
                    continue
                try:
                    ts = int(m.group(1))
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    earliest = datetime(2017, 1, 1, tzinfo=timezone.utc)
                    latest = datetime.now(timezone.utc) + timedelta(days=1)
                    if earliest <= dt <= latest:
                        return dt
                except (ValueError, OSError, OverflowError):
                    continue
        return None

    def _is_recent_enough(self, published: datetime | None) -> bool:
        """
        Only keep articles within max_age_days.
        If published is missing, return False to avoid old content slipping in.
        """
        if not published:
            return False
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=self.max_age_days)
        return published >= cutoff

    async def _resolve_final_url(
        self,
        session: aiohttp.ClientSession,
        url: str,
        headers: dict,
    ) -> str:
        """Resolve Sogou redirect URL to the final target if possible."""
        try:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                allow_redirects=False,
            ) as resp:
                if resp.status in (301, 302, 303, 307, 308):
                    location = resp.headers.get("Location", "")
                    if location:
                        return location
        except Exception as e:
            logger.debug(f"Resolve final url failed: {e}")
        return url

    async def _search_query_page(
        self,
        session: aiohttp.ClientSession,
        query: str,
        ua_index: int,
        page: int,
    ) -> list[Article]:
        """Search Sogou WeChat for a single query page."""
        articles = []
        params = {
            "type": "2",  # Article search
            "query": query,
            "ie": "utf8",
            "s_from": "input",
            "_sug_": "n",
            "_sug_type_": "",
            "page": str(page),
        }
        headers = self._build_headers(ua_index)

        try:
            async with session.get(
                SOGOU_WECHAT_URL,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                allow_redirects=False,
            ) as resp:
                if resp.status in (301, 302, 303, 307, 308):
                    location = resp.headers.get("Location", "")
                    logger.warning(f"[WeChat/{query}/p{page}] Redirected: {location}")
                    return []
                if resp.status != 200:
                    logger.warning(f"[WeChat/{query}/p{page}] HTTP {resp.status}")
                    return []
                html = await resp.text(errors="ignore")
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"[WeChat/{query}/p{page}] Fetch error: {e}")
            return []

        if self._is_antibot_page(html, str(resp.url)):
            logger.warning(f"[WeChat/{query}/p{page}] Anti-bot page detected: {resp.url}")
            return []

        soup = BeautifulSoup(html, "lxml")
        items = soup.select("div.txt-box")
        if not items:
            logger.info(f"[WeChat/{query}/p{page}] No result items found")
            return []

        for item in items:
            try:
                # Title and link
                title_tag = item.select_one("h3 a")
                if not title_tag:
                    continue
                title = title_tag.get_text(" ", strip=True)
                raw_url = title_tag.get("href", "").strip()
                if not title or not raw_url:
                    continue

                if raw_url.startswith("/"):
                    raw_url = f"https://weixin.sogou.com{raw_url}"

                # Snippet
                snippet_tag = item.select_one("p.txt-info")
                snippet = snippet_tag.get_text(" ", strip=True)[:500] if snippet_tag else ""

                # Account name
                account_tag = item.select_one("div.s-p a")
                account = account_tag.get_text(" ", strip=True) if account_tag else "WeChat"

                # Published time
                published = self._extract_timestamp(item)

                # Hard filter: discard unknown-time articles
                if not published:
                    logger.debug(
                        f"[WeChat/{query}/p{page}] Skip article without published time: {title}"
                    )
                    continue

                if not self._is_recent_enough(published):
                    cutoff = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
                    logger.debug(
                        f"[WeChat/{query}/p{page}] Skip old article "
                        f"({published.isoformat()} < {cutoff.isoformat()}): {title}"
                    )
                    continue

                # Resolve to final URL when possible
                final_url = await self._resolve_final_url(session, raw_url, headers)

                text = f"{title} {snippet}"
                topics = match_topics(text)

                articles.append(
                    Article(
                        title=title,
                        url=final_url,
                        source=f"WeChat ({account})",
                        language="zh",
                        published=published,
                        snippet=snippet,
                        topic_matches=topics,
                    )
                )
            except Exception as e:
                logger.debug(f"[WeChat/{query}/p{page}] Parse error for item: {e}")
                continue

        logger.info(
            f"[WeChat/{query}/p{page}] Scraped {len(articles)} recent articles "
            f"(max_age_days={self.max_age_days})"
        )
        return articles

    async def _search_query(
        self, session: aiohttp.ClientSession, query: str, ua_index: int
    ) -> list[Article]:
        """Search Sogou WeChat for a single query across pages."""
        results = []
        for page in range(1, self.max_pages + 1):
            page_results = await self._search_query_page(session, query, ua_index, page)
            if not page_results:
                break
            results.extend(page_results)
            if page < self.max_pages:
                await asyncio.sleep(2)
        return results

    async def fetch(self) -> list[Article]:
        """Fetch from all WeChat search queries sequentially with delays."""
        all_articles = []
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        connector = aiohttp.TCPConnector(limit=5)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Warm-up request to obtain cookies
            try:
                headers = self._build_headers(0)
                async with session.get("https://weixin.sogou.com/", headers=headers) as resp:
                    await resp.text(errors="ignore")
            except Exception:
                pass

            for i, query in enumerate(self.queries):
                results = await self._search_query(session, query, i)
                all_articles.extend(results)
                if i < len(self.queries) - 1:
                    await asyncio.sleep(2)

        # De-duplicate by final URL
        seen = set()
        deduped = []
        for article in all_articles:
            key = article.url.strip()
            if key and key not in seen:
                seen.add(key)
                deduped.append(article)

        logger.info(
            f"WeChat total: {len(deduped)} recent deduped articles "
            f"from {len(self.queries)} queries"
        )
        return deduped
