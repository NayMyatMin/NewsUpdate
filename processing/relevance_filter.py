import logging
from models.article import Article
from config.topics import match_topics, relevance_score

logger = logging.getLogger(__name__)


def filter_by_relevance(
    articles: list[Article],
    min_score: float = 2.0,
    max_articles: int = 60,
) -> list[Article]:
    """
    Pre-filter articles by keyword relevance before sending to Claude.
    This controls cost by limiting the number of articles sent to the API.
    """
    scored = []
    for article in articles:
        # Re-match topics if not already matched
        if not article.topic_matches:
            text = f"{article.title} {article.snippet or ''}"
            article.topic_matches = match_topics(text)

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
