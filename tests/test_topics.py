"""Tests for topic matching and scoring."""

from config.topics import match_topics, relevance_score, get_all_keywords, TOPICS


class TestTopicConfig:
    def test_all_topics_have_required_fields(self):
        for topic_id, topic in TOPICS.items():
            assert "label" in topic, f"{topic_id} missing label"
            assert "weight" in topic, f"{topic_id} missing weight"
            assert "keywords_en" in topic, f"{topic_id} missing keywords_en"
            assert "keywords_zh" in topic, f"{topic_id} missing keywords_zh"
            assert topic["weight"] > 0, f"{topic_id} has non-positive weight"
            assert len(topic["keywords_en"]) > 0, f"{topic_id} has no English keywords"
            assert len(topic["keywords_zh"]) > 0, f"{topic_id} has no Chinese keywords"

    def test_weight_tiers(self):
        high = [t for t in TOPICS.values() if t["weight"] == 3.0]
        medium_high = [t for t in TOPICS.values() if t["weight"] == 2.5]
        assert len(high) >= 3, "Should have at least 3 high-priority topics"
        assert len(medium_high) >= 3, "Should have at least 3 medium-high topics"


class TestMatchTopics:
    def test_english_match(self):
        topics = match_topics("AI safety is critical for alignment research")
        assert "ai_safety" in topics

    def test_chinese_match(self):
        topics = match_topics("华为发布最新鸿蒙系统更新")
        assert "huawei_ecosystem" in topics

    def test_no_match(self):
        topics = match_topics("The weather is nice today")
        assert len(topics) == 0

    def test_multiple_matches(self):
        text = "Huawei AI safety evaluation for large language model security"
        topics = match_topics(text)
        assert len(topics) >= 2


class TestRelevanceScore:
    def test_high_priority_scores_high(self):
        score = relevance_score(["ai_safety", "ai_security", "huawei_ecosystem"])
        assert score == 9.0  # 3.0 * 3

    def test_empty_topics(self):
        assert relevance_score([]) == 0.0

    def test_single_topic(self):
        score = relevance_score(["ai_safety"])
        assert score == 3.0

    def test_invalid_topic_ignored(self):
        score = relevance_score(["ai_safety", "nonexistent_topic"])
        assert score == 3.0


class TestGetAllKeywords:
    def test_returns_both_languages(self):
        keywords = get_all_keywords()
        assert "en" in keywords
        assert "zh" in keywords
        assert len(keywords["en"]) > 50
        assert len(keywords["zh"]) > 20
