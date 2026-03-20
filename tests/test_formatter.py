"""Tests for output formatters."""

from datetime import datetime, timezone
from models.article import RankedArticle, Digest
from output.formatter import format_digest_markdown, format_digest_terminal


def _make_digest() -> Digest:
    articles = [
        RankedArticle(
            title="Critical AI Safety Breakthrough",
            url="https://example.com/ai-safety",
            source="TestSource",
            language="en",
            rank=1,
            relevance_score=9.5,
            summary="Major advancement in AI safety research.",
            why_important="Could reshape alignment approaches.",
            topic_matches=["ai_safety"],
        ),
        RankedArticle(
            title="华为发布新AI芯片",
            url="https://example.com/huawei",
            source="36Kr",
            language="zh",
            rank=2,
            relevance_score=8.0,
            summary="Huawei releases next-gen AI chip.",
            why_important="Competitive implications.",
            topic_matches=["huawei_ecosystem"],
        ),
    ]
    return Digest(
        date="2026-03-20",
        generated_at=datetime(2026, 3, 20, 7, 0, tzinfo=timezone.utc),
        total_fetched=1400,
        total_after_dedup=1200,
        total_after_filter=80,
        top_articles=articles,
    )


class TestMarkdownFormatter:
    def test_contains_header(self):
        md = format_digest_markdown(_make_digest())
        assert "# AI Safety News Digest" in md
        assert "2026-03-20" in md

    def test_contains_articles(self):
        md = format_digest_markdown(_make_digest())
        assert "Critical AI Safety Breakthrough" in md
        assert "华为发布新AI芯片" in md

    def test_contains_metadata(self):
        md = format_digest_markdown(_make_digest())
        assert "1400 articles fetched" in md
        assert "1200 after dedup" in md

    def test_contains_scores(self):
        md = format_digest_markdown(_make_digest())
        assert "9.5" in md


class TestTerminalFormatter:
    def test_contains_header(self):
        out = format_digest_terminal(_make_digest())
        assert "AI SAFETY NEWS DIGEST" in out
        assert "2026-03-20" in out

    def test_contains_articles(self):
        out = format_digest_terminal(_make_digest())
        assert "Critical AI Safety Breakthrough" in out

    def test_contains_pipeline_stats(self):
        out = format_digest_terminal(_make_digest())
        assert "1400 fetched" in out
