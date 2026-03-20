"""Tests for the deduplication pipeline."""

from datetime import datetime, timezone
from models.article import Article
from processing.deduplicator import (
    _dedup_by_url,
    _dedup_by_jaccard,
    _jaccard_similarity,
    _cosine_similarity,
    _tokenize,
)


def _make_article(title: str, url: str = "", source: str = "test", lang: str = "en") -> Article:
    return Article(
        title=title,
        url=url or f"https://example.com/{title.replace(' ', '-')}",
        source=source,
        language=lang,
    )


class TestURLDedup:
    def test_removes_exact_duplicates(self):
        articles = [
            _make_article("Article A", url="https://example.com/a"),
            _make_article("Article B", url="https://example.com/a"),
        ]
        result = _dedup_by_url(articles)
        assert len(result) == 1
        assert result[0].title == "Article A"

    def test_normalizes_trailing_slash(self):
        articles = [
            _make_article("A", url="https://example.com/a"),
            _make_article("B", url="https://example.com/a/"),
        ]
        result = _dedup_by_url(articles)
        assert len(result) == 1

    def test_case_insensitive(self):
        articles = [
            _make_article("A", url="https://Example.COM/Page"),
            _make_article("B", url="https://example.com/page"),
        ]
        result = _dedup_by_url(articles)
        assert len(result) == 1

    def test_keeps_different_urls(self):
        articles = [
            _make_article("A", url="https://example.com/a"),
            _make_article("B", url="https://example.com/b"),
        ]
        result = _dedup_by_url(articles)
        assert len(result) == 2


class TestJaccardDedup:
    def test_removes_similar_titles(self):
        articles = [
            _make_article("OpenAI releases GPT-5 with new safety features"),
            _make_article("OpenAI releases GPT-5 with new safety features today"),
        ]
        result = _dedup_by_jaccard(articles, jaccard_threshold=0.6)
        assert len(result) == 1

    def test_keeps_different_titles(self):
        articles = [
            _make_article("OpenAI releases GPT-5"),
            _make_article("Huawei launches new Ascend chip"),
        ]
        result = _dedup_by_jaccard(articles, jaccard_threshold=0.6)
        assert len(result) == 2

    def test_empty_list(self):
        result = _dedup_by_jaccard([], jaccard_threshold=0.6)
        assert len(result) == 0

    def test_single_article(self):
        articles = [_make_article("Solo article")]
        result = _dedup_by_jaccard(articles, jaccard_threshold=0.6)
        assert len(result) == 1


class TestSimilarityFunctions:
    def test_jaccard_identical(self):
        tokens = {"hello", "world"}
        assert _jaccard_similarity(tokens, tokens) == 1.0

    def test_jaccard_disjoint(self):
        a = {"hello", "world"}
        b = {"foo", "bar"}
        assert _jaccard_similarity(a, b) == 0.0

    def test_jaccard_partial(self):
        a = {"hello", "world", "foo"}
        b = {"hello", "world", "bar"}
        sim = _jaccard_similarity(a, b)
        assert 0.4 < sim < 0.6  # 2/4 = 0.5

    def test_jaccard_empty(self):
        assert _jaccard_similarity(set(), {"hello"}) == 0.0
        assert _jaccard_similarity(set(), set()) == 0.0

    def test_cosine_identical(self):
        v = [1.0, 2.0, 3.0]
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6

    def test_cosine_orthogonal(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(_cosine_similarity(a, b)) < 1e-6

    def test_cosine_zero_vector(self):
        assert _cosine_similarity([0, 0], [1, 2]) == 0.0

    def test_tokenize(self):
        tokens = _tokenize("Hello World Test")
        assert tokens == {"hello", "world", "test"}
