"""
Filter out stale articles that are older than a configurable max age.
"""

import logging
from datetime import datetime, timedelta, timezone

from config.settings import MAX_ARTICLE_AGE_HOURS
from models.article import Article

logger = logging.getLogger(__name__)


def filter_by_freshness(
    articles: list[Article],
    max_age_hours: int = MAX_ARTICLE_AGE_HOURS,
) -> list[Article]:
    """Remove articles whose published date is older than max_age_hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    fresh = []
    stale_count = 0

    for article in articles:
        if article.published is None:
            # No date available — keep it (benefit of the doubt)
            fresh.append(article)
        elif article.published.tzinfo is None:
            # Naive datetime — assume UTC
            if article.published.replace(tzinfo=timezone.utc) >= cutoff:
                fresh.append(article)
            else:
                stale_count += 1
        elif article.published >= cutoff:
            fresh.append(article)
        else:
            stale_count += 1

    logger.info(
        f"Freshness filter: {len(articles)} -> {len(fresh)} "
        f"(dropped {stale_count} older than {max_age_hours}h)"
    )
    return fresh
