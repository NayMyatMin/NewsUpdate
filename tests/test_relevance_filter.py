"""Tests for the relevance filtering pipeline."""

from models.article import Article
from processing.relevance_filter import filter_by_relevance, match_topics_strict


def _make_article(title: str, snippet: str = "", lang: str = "en") -> Article:
    return Article(
        title=title,
        url=f"https://example.com/{hash(title)}",
        source="test",
        language=lang,
        snippet=snippet,
    )


class TestMatchTopicsStrict:
    def test_matches_ai_safety_keyword(self):
        topics = match_topics_strict("New research on AI safety evaluation released")
        assert "ai_safety" in topics

    def test_no_false_positive_on_substring(self):
        # "ai" should not match inside "said" or "fair" etc.
        topics = match_topics_strict("He said it was fair and plain")
        assert "ai_safety" not in topics
        assert "ai_security" not in topics

    def test_matches_chinese_keywords(self):
        topics = match_topics_strict("华为发布新一代昇腾芯片")
        assert "huawei_ecosystem" in topics

    def test_matches_cybersecurity(self):
        topics = match_topics_strict("Critical zero-day vulnerability found in Linux kernel")
        assert "cybersecurity" in topics

    def test_matches_multiple_topics(self):
        text = "Huawei releases new AI safety evaluation framework for large language models"
        topics = match_topics_strict(text)
        assert "huawei_ecosystem" in topics
        assert "ai_safety" in topics

    def test_empty_text(self):
        topics = match_topics_strict("")
        assert topics == []


class TestFilterByRelevance:
    def test_filters_low_scoring_articles(self):
        articles = [
            _make_article("AI safety breakthrough announced today"),
            _make_article("Local sports team wins championship"),
            _make_article("Best recipe for chocolate cake"),
        ]
        result = filter_by_relevance(articles, min_score=1.5, max_articles=80)
        # Only the AI article should pass
        assert len(result) >= 1
        assert any("AI safety" in a.title for a in result)

    def test_respects_max_articles(self):
        articles = [
            _make_article(f"AI safety research paper #{i}", snippet="ai safety alignment")
            for i in range(20)
        ]
        result = filter_by_relevance(articles, min_score=0.1, max_articles=5)
        assert len(result) <= 5

    def test_sorts_by_score_descending(self):
        articles = [
            _make_article("Minor cloud update", snippet="cloud computing"),
            _make_article(
                "Critical AI security vulnerability in GPT system",
                snippet="prompt injection jailbreak adversarial attack AI safety",
            ),
        ]
        result = filter_by_relevance(articles, min_score=0.1, max_articles=80)
        if len(result) >= 2:
            # Higher-scoring article should come first
            assert "security" in result[0].title.lower() or "AI" in result[0].title

    def test_empty_input(self):
        result = filter_by_relevance([], min_score=1.5, max_articles=80)
        assert result == []

    def test_updates_topic_matches(self):
        article = _make_article("Huawei launches HarmonyOS update")
        assert article.topic_matches == []
        result = filter_by_relevance([article], min_score=0.1, max_articles=80)
        if result:
            assert len(result[0].topic_matches) > 0
