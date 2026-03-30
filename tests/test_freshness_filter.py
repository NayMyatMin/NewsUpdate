"""Tests for the freshness filtering pipeline."""

from datetime import datetime, timedelta, timezone

from models.article import Article
from processing.freshness_filter import filter_by_freshness


def _make_article(title: str, published: datetime | None = None) -> Article:
    return Article(
        title=title,
        url=f"https://example.com/{hash(title)}",
        source="test",
        language="en",
        published=published,
    )


class TestFilterByFreshness:
    def test_keeps_recent_articles(self):
        now = datetime.now(timezone.utc)
        articles = [_make_article("Recent news", now - timedelta(hours=1))]
        result = filter_by_freshness(articles, max_age_hours=48)
        assert len(result) == 1

    def test_drops_stale_articles(self):
        old = datetime.now(timezone.utc) - timedelta(days=365)
        articles = [_make_article("Old news", old)]
        result = filter_by_freshness(articles, max_age_hours=48)
        assert len(result) == 0

    def test_keeps_articles_without_date(self):
        articles = [_make_article("No date", None)]
        result = filter_by_freshness(articles, max_age_hours=48)
        assert len(result) == 1

    def test_handles_naive_datetime(self):
        recent_naive = datetime.utcnow() - timedelta(hours=1)
        articles = [_make_article("Naive datetime", recent_naive)]
        result = filter_by_freshness(articles, max_age_hours=48)
        assert len(result) == 1

    def test_drops_naive_old_datetime(self):
        old_naive = datetime.utcnow() - timedelta(days=30)
        articles = [_make_article("Old naive", old_naive)]
        result = filter_by_freshness(articles, max_age_hours=48)
        assert len(result) == 0

    def test_boundary_just_inside_cutoff(self):
        # 1 second inside the cutoff window should be kept
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=48) + timedelta(seconds=5)
        articles = [_make_article("Boundary", cutoff_time)]
        result = filter_by_freshness(articles, max_age_hours=48)
        assert len(result) == 1

    def test_mixed_fresh_and_stale(self):
        now = datetime.now(timezone.utc)
        articles = [
            _make_article("Fresh 1", now - timedelta(hours=1)),
            _make_article("Stale 1", now - timedelta(days=365)),
            _make_article("Fresh 2", now - timedelta(hours=24)),
            _make_article("Stale 2", now - timedelta(days=1800)),
        ]
        result = filter_by_freshness(articles, max_age_hours=48)
        assert len(result) == 2
        assert all("Fresh" in a.title for a in result)

    def test_empty_input(self):
        result = filter_by_freshness([], max_age_hours=48)
        assert result == []
