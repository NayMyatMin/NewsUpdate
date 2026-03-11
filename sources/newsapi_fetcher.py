import asyncio
import logging
from datetime import datetime, timedelta, timezone

import aiohttp

from config.settings import NEWSAPI_KEY
from config.topics import match_topics
from models.article import Article
from sources.base import BaseFetcher

logger = logging.getLogger(__name__)

# Topic queries for NewsAPI (max ~8 to stay within free tier limits)
NEWSAPI_QUERIES = [
    "AI safety OR AI alignment",
    "AI security OR adversarial attack OR prompt injection",
    "large language model OR LLM",
    "AI agent OR autonomous agent",
    "Huawei AI OR HarmonyOS",
    "AI regulation OR AI governance",
    "deepfake OR AI cybersecurity",
    "AI chip OR semiconductor export",
]


class NewsAPIFetcher(BaseFetcher):
    """Fetches news from NewsAPI.org (free tier: 100 req/day)."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.base_url = "https://newsapi.org/v2/everything"

    async def fetch(self) -> list[Article]:
        if not NEWSAPI_KEY:
            logger.info("NewsAPI key not configured, skipping")
            return []

        all_articles = []
        yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")

        async with aiohttp.ClientSession() as session:
            for query in NEWSAPI_QUERIES:
                try:
                    params = {
                        "q": query,
                        "from": yesterday,
                        "sortBy": "publishedAt",
                        "language": "en",
                        "pageSize": 20,
                        "apiKey": NEWSAPI_KEY,
                    }
                    async with session.get(
                        self.base_url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as resp:
                        if resp.status != 200:
                            logger.warning(f"NewsAPI HTTP {resp.status} for query: {query}")
                            continue
                        data = await resp.json()
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.warning(f"NewsAPI error for '{query}': {e}")
                    continue

                for item in data.get("articles", []):
                    title = (item.get("title") or "").strip()
                    url = (item.get("url") or "").strip()
                    if not title or not url or title == "[Removed]":
                        continue

                    published = None
                    if item.get("publishedAt"):
                        try:
                            published = datetime.fromisoformat(
                                item["publishedAt"].replace("Z", "+00:00")
                            )
                        except ValueError:
                            pass

                    snippet = (item.get("description") or "")[:500]
                    text = f"{title} {snippet}"
                    topics = match_topics(text)

                    all_articles.append(Article(
                        title=title,
                        url=url,
                        source=f"NewsAPI ({item.get('source', {}).get('name', 'Unknown')})",
                        language="en",
                        published=published,
                        snippet=snippet,
                        topic_matches=topics,
                    ))

        logger.info(f"NewsAPI fetched {len(all_articles)} articles total")
        return all_articles
