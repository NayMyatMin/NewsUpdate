import logging
from models.article import Article

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> set[str]:
    """Simple whitespace tokenizer for similarity comparison."""
    return set(text.lower().split())


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    """Calculate Jaccard similarity between two token sets."""
    if not a or not b:
        return 0.0
    intersection = a & b
    union = a | b
    return len(intersection) / len(union)


def deduplicate(articles: list[Article], similarity_threshold: float = 0.6) -> list[Article]:
    """
    Remove duplicate articles by:
    1. Exact URL dedup
    2. Title similarity (Jaccard) dedup
    """
    # Step 1: URL dedup
    seen_urls = set()
    url_deduped = []
    for article in articles:
        normalized_url = article.url.rstrip("/").lower()
        if normalized_url not in seen_urls:
            seen_urls.add(normalized_url)
            url_deduped.append(article)

    logger.info(f"URL dedup: {len(articles)} -> {len(url_deduped)}")

    # Step 2: Title similarity dedup
    final = []
    title_tokens_list: list[set[str]] = []

    for article in url_deduped:
        tokens = _tokenize(article.title)
        is_dup = False
        for existing_tokens in title_tokens_list:
            if _jaccard_similarity(tokens, existing_tokens) > similarity_threshold:
                is_dup = True
                break
        if not is_dup:
            final.append(article)
            title_tokens_list.append(tokens)

    logger.info(f"Title similarity dedup: {len(url_deduped)} -> {len(final)}")
    return final
