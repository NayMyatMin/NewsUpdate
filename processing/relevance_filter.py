"""
Pre-filter articles by keyword relevance before sending to LLM.
Uses word-boundary matching to avoid false positives (e.g., "ai" in "said").
"""

import logging
import re
from models.article import Article
from config.topics import match_topics, relevance_score

logger = logging.getLogger(__name__)

# Precompile word-boundary patterns for English keywords
_word_boundary_cache: dict[str, re.Pattern] = {}


def _matches_keyword(keyword: str, text_lower: str, text_original: str) -> bool:
    """Check if keyword appears in text, using word boundaries for English."""
    # Chinese keywords: substring match on original text (no word boundaries)
    if any("\u4e00" <= ch <= "\u9fff" for ch in keyword):
        return keyword in text_original

    # English keywords: word-boundary match to avoid false positives
    if keyword not in _word_boundary_cache:
        escaped = re.escape(keyword.lower())
        _word_boundary_cache[keyword] = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
    return bool(_word_boundary_cache[keyword].search(text_lower))


def match_topics_strict(text: str) -> list[str]:
    """Match topics using word-boundary matching for English keywords."""
    from config.topics import TOPICS

    text_lower = text.lower()
    matched = []
    for topic_id, topic in TOPICS.items():
        found = False
        for kw in topic["keywords_en"]:
            if _matches_keyword(kw, text_lower, text):
                found = True
                break
        if not found:
            for kw in topic["keywords_zh"]:
                if _matches_keyword(kw, text_lower, text):
                    found = True
                    break
        if found:
            matched.append(topic_id)
    return matched


def filter_by_relevance(
    articles: list[Article],
    min_score: float = 2.0,
    max_articles: int = 80,
) -> list[Article]:
    """
    Pre-filter articles by keyword relevance before sending to LLM.
    Uses word-boundary matching for English to reduce false positives.
    Controls cost by capping the number of articles sent to the API.
    """
    scored = []
    for article in articles:
        # Re-match topics with strict matching
        text = f"{article.title} {article.snippet or ''}"
        article.topic_matches = match_topics_strict(text)

        score = relevance_score(article.topic_matches)
        if score >= min_score:
            scored.append((score, article))

    # Sort by score descending, take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    filtered = [article for _, article in scored[:max_articles]]

    logger.info(
        f"Relevance filter: {len(articles)} -> {len(filtered)} "
        f"(min_score={min_score}, max={max_articles})"
    )
    return filtered
