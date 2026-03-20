"""Tests for Pydantic data models."""

from datetime import datetime, timezone
from models.article import Article, RankedArticle, Digest


class TestArticleModel:
    def test_defaults(self):
        a = Article(title="Test", url="https://example.com", source="test")
        assert a.language == "en"
        assert a.published is None
        assert a.snippet is None
        assert a.topic_matches == []

    def test_full_article(self):
        now = datetime.now(timezone.utc)
        a = Article(
            title="Test Article",
            url="https://example.com/test",
            source="TestSource",
            language="zh",
            published=now,
            snippet="A test snippet",
            topic_matches=["ai_safety", "cybersecurity"],
        )
        assert a.title == "Test Article"
        assert a.language == "zh"
        assert len(a.topic_matches) == 2


class TestRankedArticleModel:
    def test_defaults(self):
        a = RankedArticle(title="Test", url="https://example.com", source="test")
        assert a.rank == 0
        assert a.relevance_score == 0.0
        assert a.summary == ""
        assert a.why_important == ""

    def test_ranked_fields(self):
        a = RankedArticle(
            title="Test",
            url="https://example.com",
            source="test",
            rank=1,
            relevance_score=9.5,
            summary="Important finding",
            why_important="Changes the landscape",
        )
        assert a.rank == 1
        assert a.relevance_score == 9.5


class TestDigestModel:
    def test_digest(self):
        now = datetime.now(timezone.utc)
        ranked = RankedArticle(
            title="Test", url="https://example.com", source="test",
            rank=1, relevance_score=8.0,
        )
        d = Digest(
            date="2026-03-20",
            generated_at=now,
            total_fetched=1000,
            total_after_dedup=800,
            total_after_filter=80,
            top_articles=[ranked],
        )
        assert d.total_fetched == 1000
        assert len(d.top_articles) == 1
