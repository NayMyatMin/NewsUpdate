"""
Cross-lingual deduplication using embeddings + cosine similarity.

Two-pass approach:
  1. Exact URL dedup (free, instant)
  2. Embedding-based semantic dedup (catches cross-lingual duplicates)

Falls back to Jaccard title similarity when no embedding API is available.
"""

import logging
import math
from models.article import Article

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> set[str]:
    """Simple whitespace tokenizer for fallback similarity."""
    return set(text.lower().split())


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors (pure Python, no numpy needed)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _get_embeddings(texts: list[str]) -> list[list[float]] | None:
    """Get embeddings via OpenAI API. Returns None if unavailable."""
    from config.settings import OPENAI_API_KEY, OPENAI_BASE_URL, EMBEDDING_MODEL

    if not OPENAI_API_KEY:
        return None

    try:
        import openai

        kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            kwargs["base_url"] = OPENAI_BASE_URL

        client = openai.OpenAI(**kwargs)

        # Process in batches of 100 (API limit is 2048 but keep it safe)
        all_embeddings = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings
    except Exception as e:
        logger.warning(f"Embedding API unavailable, falling back to Jaccard: {e}")
        return None


def _dedup_by_url(articles: list[Article]) -> list[Article]:
    """Remove exact URL duplicates."""
    seen_urls = set()
    result = []
    for article in articles:
        normalized = article.url.rstrip("/").lower()
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            result.append(article)
    logger.info(f"URL dedup: {len(articles)} -> {len(result)}")
    return result


def _dedup_by_embedding(
    articles: list[Article], similarity_threshold: float
) -> list[Article]:
    """Semantic dedup using multilingual embeddings + cosine similarity."""
    # Build text for embedding: title + first 200 chars of snippet
    texts = []
    for a in articles:
        snippet_prefix = (a.snippet or "")[:200]
        texts.append(f"{a.title} {snippet_prefix}".strip())

    embeddings = _get_embeddings(texts)
    if embeddings is None:
        logger.info("No embeddings available, falling back to Jaccard dedup")
        return _dedup_by_jaccard(articles, jaccard_threshold=0.6)

    logger.info(f"Got {len(embeddings)} embeddings, running semantic dedup "
                f"(threshold={similarity_threshold})")

    # Greedy dedup: keep article if it's not too similar to any already-kept article
    kept_indices: list[int] = []
    kept_embeddings: list[list[float]] = []

    for i, emb in enumerate(embeddings):
        is_dup = False
        for kept_emb in kept_embeddings:
            if _cosine_similarity(emb, kept_emb) > similarity_threshold:
                is_dup = True
                break
        if not is_dup:
            kept_indices.append(i)
            kept_embeddings.append(emb)

    result = [articles[i] for i in kept_indices]
    logger.info(f"Embedding dedup: {len(articles)} -> {len(result)}")
    return result


def _dedup_by_jaccard(
    articles: list[Article], jaccard_threshold: float = 0.6
) -> list[Article]:
    """Fallback: title similarity dedup using Jaccard index."""
    result = []
    title_tokens_list: list[set[str]] = []

    for article in articles:
        tokens = _tokenize(article.title)
        is_dup = False
        for existing_tokens in title_tokens_list:
            if _jaccard_similarity(tokens, existing_tokens) > jaccard_threshold:
                is_dup = True
                break
        if not is_dup:
            result.append(article)
            title_tokens_list.append(tokens)

    logger.info(f"Jaccard dedup: {len(articles)} -> {len(result)}")
    return result


def deduplicate(
    articles: list[Article],
    similarity_threshold: float = 0.82,
) -> list[Article]:
    """
    Remove duplicate articles using a two-pass approach:
    1. Exact URL dedup (instant, free)
    2. Embedding-based semantic dedup (catches cross-lingual duplicates)
       Falls back to Jaccard if embedding API unavailable.
    """
    from config.settings import DEDUP_SIMILARITY_THRESHOLD
    threshold = similarity_threshold if similarity_threshold != 0.82 else DEDUP_SIMILARITY_THRESHOLD

    # Pass 1: URL dedup
    articles = _dedup_by_url(articles)

    if len(articles) <= 1:
        return articles

    # Pass 2: Semantic dedup
    articles = _dedup_by_embedding(articles, threshold)

    return articles
