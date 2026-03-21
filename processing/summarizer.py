"""
Two-tier LLM summarization and ranking.

L1 (cheap model): Fast screening of all filtered articles. Scores 0-10,
   keeps only articles scoring >= 5.0 for deeper analysis.
L2 (strong model): Deep analysis of L1 survivors. Generates detailed
   summaries and final ranking.

Falls back to keyword-only ranking when no API key is configured.
"""

import json
import logging

from config.settings import (
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_BASE_URL,
    L2_ENABLED,
    L2_OPENAI_MODEL,
    L2_ANTHROPIC_MODEL,
    L1_PASS_COUNT,
    EVENT_DEDUP_THRESHOLD,
)
from models.article import Article, RankedArticle
from processing.deduplicator import _get_embeddings, _cosine_similarity

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a tech news analyst for an AI Safety researcher at Huawei.
Your job is to evaluate news articles and identify the most important ones across
ALL areas of technology, security, and AI.

The researcher needs to stay up-to-date on:
- AI safety, alignment, and responsible AI
- AI security (adversarial attacks, prompt injection, jailbreaking, red teaming)
- Large language models and frontier AI development
- AI agents and agentic AI systems
- AI governance, regulation, and policy (China and international)
- Huawei ecosystem (HarmonyOS, Ascend, MindSpore, Kunpeng)
- Geopolitical AI competition (US-China, chip export controls)
- Cybersecurity: data breaches, ransomware, zero-days, APTs, security incidents
- Vulnerability disclosures, CVEs, exploit chains, patch advisories
- Cloud computing, infrastructure, DevOps, Kubernetes
- Mobile/telecom AI and on-device AI
- Open-source AI models (DeepSeek, Qwen, LLaMA, etc.)
- Software development tools, programming languages, open source
- Privacy, data protection, surveillance tech
- Quantum computing, blockchain, robotics, hardware
- Big tech company moves, acquisitions, major product launches

Be especially attentive to:
1. Breaking security incidents and active exploits (highest urgency)
2. Breaking developments that shift the AI safety landscape
3. New vulnerabilities or attack methods (on AI systems or general infra)
4. Regulatory changes in China or internationally
5. Huawei-specific news and competitor moves
6. Major model releases or capability breakthroughs
7. Critical infrastructure outages or cloud incidents"""

# L1: fast screening prompt — only needs a score, no summaries
L1_PROMPT_TEMPLATE = """Quickly evaluate these {count} news articles. For each, provide ONLY:
- relevance_score (0.0-10.0): How important for a tech-savvy AI safety researcher at Huawei

Scoring guide:
- 9-10: Active security incident, critical AI safety breakthrough, major Huawei news, critical zero-day
- 7-8: Significant AI advance, new vulnerability/CVE, important regulatory action, major breach
- 5-6: Notable tech industry news, cloud/infra updates, interesting research
- 3-4: Minor tech updates, tangential news
- 0-2: Not relevant

Articles:
{articles_json}

Respond ONLY with a valid JSON array: [{{"index": 0, "relevance_score": 8.5}}, ...]"""

# L2: deep analysis prompt — full summaries for top candidates
L2_PROMPT_TEMPLATE = """Analyze these {count} high-priority news articles in depth.

IMPORTANT: You MUST return an entry for ALL {count} articles. Do not skip any.

For each article, provide:
1. relevance_score (0.0-10.0): Final importance score after deep analysis
2. summary (2-3 sentences): Key facts, technical details, and implications
3. why_important (1 sentence): Why this specifically matters for AI safety research at Huawei

Scoring guide:
- 9-10: Active security incident, critical AI safety breakthrough, major Huawei news, or critical zero-day
- 7-8: Significant AI advance, new vulnerability/CVE, important regulatory action, major breach
- 5-6: Notable tech industry news, cloud/infra updates, interesting research

Articles:
{articles_json}

Respond ONLY with a valid JSON array of exactly {count} elements. Each element must have:
"index", "relevance_score", "summary", "why_important"

Example: [{{"index": 0, "relevance_score": 8.5, "summary": "...", "why_important": "..."}}]"""


def _format_articles_for_prompt(articles: list[Article], max_snippet: int = 300) -> str:
    """Format articles as a numbered JSON list for the prompt."""
    items = []
    for i, a in enumerate(articles):
        items.append({
            "index": i,
            "title": a.title,
            "source": a.source,
            "language": a.language,
            "snippet": (a.snippet or "")[:max_snippet],
            "url": a.url,
        })
    return json.dumps(items, ensure_ascii=False, indent=2)


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return text


def _call_anthropic(
    system: str, user_prompt: str, model: str | None = None, max_tokens: int = 4096
) -> str:
    """Call Anthropic Claude API and return response text."""
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=model or ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text.strip()


def _call_openai(
    system: str, user_prompt: str, model: str | None = None, max_tokens: int = 4096
) -> str:
    """Call OpenAI (or compatible) API and return response text."""
    import openai

    kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL

    client = openai.OpenAI(**kwargs)
    resolved_model = model or OPENAI_MODEL
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = client.chat.completions.create(
            model=resolved_model,
            max_completion_tokens=max_tokens,
            messages=messages,
        )
    except openai.BadRequestError as e:
        if "max_completion_tokens" in str(e):
            # Older model/API that only supports max_tokens
            response = client.chat.completions.create(
                model=resolved_model,
                max_tokens=max_tokens,
                messages=messages,
            )
        else:
            raise
    return response.choices[0].message.content.strip()


def _call_llm(
    system: str, user_prompt: str, model: str | None = None, max_tokens: int = 4096
) -> str:
    """Route to the configured LLM provider."""
    if LLM_PROVIDER == "openai":
        return _call_openai(system, user_prompt, model, max_tokens)
    else:
        return _call_anthropic(system, user_prompt, model, max_tokens)


def _has_api_key() -> bool:
    """Check if the configured provider has an API key."""
    if LLM_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    return bool(ANTHROPIC_API_KEY)


def _parse_llm_json(response_text: str) -> list[dict]:
    """Parse LLM response as JSON array, handling common issues."""
    cleaned = _strip_code_fences(response_text)
    return json.loads(cleaned)


async def _run_l1_screening(
    articles: list[Article],
    batch_size: int = 25,
) -> list[tuple[float, int]]:
    """
    L1: Fast screening with cheap model.
    Returns list of (score, original_index) for all articles.
    """
    l1_model = OPENAI_MODEL if LLM_PROVIDER == "openai" else ANTHROPIC_MODEL
    logger.info(f"L1 screening {len(articles)} articles with {l1_model}")

    all_scored: list[tuple[float, int]] = []

    for batch_start in range(0, len(articles), batch_size):
        batch = articles[batch_start : batch_start + batch_size]
        # L1 only needs title + short snippet for speed
        articles_json = _format_articles_for_prompt(batch, max_snippet=200)

        prompt = L1_PROMPT_TEMPLATE.format(
            count=len(batch),
            articles_json=articles_json,
        )

        try:
            response_text = _call_llm(SYSTEM_PROMPT, prompt, model=l1_model)
            results = _parse_llm_json(response_text)

            for item in results:
                idx = item.get("index", 0)
                global_idx = batch_start + idx
                score = float(item.get("relevance_score", 0))
                all_scored.append((score, global_idx))

        except json.JSONDecodeError as e:
            logger.error(f"L1 JSON parse error: {e}")
            for i in range(len(batch)):
                all_scored.append((0, batch_start + i))
        except Exception as e:
            logger.error(f"L1 API error: {e}")
            for i in range(len(batch)):
                all_scored.append((0, batch_start + i))

    return all_scored


async def _run_l2_deep_analysis(
    articles: list[Article],
    original_indices: list[int],
    l1_scores: list[float],
) -> list[tuple[float, int, dict]]:
    """
    L2: Deep analysis with strong model on L1 survivors.
    Returns list of (score, original_index, llm_result).
    """
    l2_model = None
    if L2_ENABLED:
        l2_model = L2_OPENAI_MODEL if LLM_PROVIDER == "openai" else L2_ANTHROPIC_MODEL
        logger.info(f"L2 deep analysis on {len(articles)} articles with {l2_model}")
    else:
        l2_model = OPENAI_MODEL if LLM_PROVIDER == "openai" else ANTHROPIC_MODEL
        logger.info(f"L2 disabled, using L1 model {l2_model} for summaries")

    # L2 gets full snippet for deeper analysis
    articles_json = _format_articles_for_prompt(articles, max_snippet=500)

    prompt = L2_PROMPT_TEMPLATE.format(
        count=len(articles),
        articles_json=articles_json,
    )

    all_scored: list[tuple[float, int, dict]] = []

    try:
        response_text = _call_llm(SYSTEM_PROMPT, prompt, model=l2_model, max_tokens=8192)
        results = _parse_llm_json(response_text)

        seen_indices = set()
        for item in results:
            idx = item.get("index", 0)
            if idx < len(original_indices):
                orig_idx = original_indices[idx]
                score = float(item.get("relevance_score", 0))
                all_scored.append((score, orig_idx, item))
                seen_indices.add(idx)

        # Backfill any articles the LLM skipped, using L1 scores
        for i, (orig_idx, l1_score) in enumerate(zip(original_indices, l1_scores)):
            if i not in seen_indices:
                logger.warning(f"L2 skipped article index {i}, backfilling with L1 score {l1_score}")
                all_scored.append((l1_score, orig_idx, {}))

    except json.JSONDecodeError as e:
        logger.error(f"L2 JSON parse error: {e}")
        # Fall back to L1 scores with no summaries
        for i, (orig_idx, l1_score) in enumerate(zip(original_indices, l1_scores)):
            all_scored.append((l1_score, orig_idx, {}))
    except Exception as e:
        logger.error(f"L2 API error: {e}")
        for i, (orig_idx, l1_score) in enumerate(zip(original_indices, l1_scores)):
            all_scored.append((l1_score, orig_idx, {}))

    return all_scored


def _dedup_by_event(
    scored_results: list[tuple[float, int, dict]],
    articles: list[Article],
    similarity_threshold: float,
) -> list[tuple[float, int, dict]]:
    """
    Post-L2 event-level dedup: remove articles covering the same event.

    Iterates results in score order (highest first). For each article, checks
    embedding similarity of its title against all already-kept articles. If too
    similar to any kept article, it's skipped as a duplicate event.
    """
    if not scored_results:
        return scored_results

    # Build title texts for embedding (title + short summary for better matching)
    texts = []
    for score, idx, llm_result in scored_results:
        title = articles[idx].title if idx < len(articles) else ""
        summary = llm_result.get("summary", "")[:150]
        texts.append(f"{title} {summary}".strip())

    embeddings = _get_embeddings(texts)

    if embeddings is None:
        # Fallback: simple title-token overlap dedup
        logger.info("No embeddings for event dedup, falling back to title overlap")
        kept: list[tuple[float, int, dict]] = []
        kept_title_tokens: list[set[str]] = []
        for i, (score, idx, llm_result) in enumerate(scored_results):
            title = articles[idx].title if idx < len(articles) else ""
            tokens = set(title.lower().split())
            is_dup = False
            for existing in kept_title_tokens:
                if tokens and existing:
                    overlap = len(tokens & existing) / len(tokens | existing)
                    if overlap > 0.4:
                        is_dup = True
                        break
            if not is_dup:
                kept.append((score, idx, llm_result))
                kept_title_tokens.append(tokens)
        logger.info(f"Event dedup (title fallback): {len(scored_results)} -> {len(kept)}")
        return kept

    # Greedy dedup using embeddings: keep if not too similar to any already-kept
    kept = []
    kept_embeddings: list[list[float]] = []

    for i, (score, idx, llm_result) in enumerate(scored_results):
        emb = embeddings[i]
        is_dup = False
        for kept_emb in kept_embeddings:
            if _cosine_similarity(emb, kept_emb) > similarity_threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append((score, idx, llm_result))
            kept_embeddings.append(emb)
        else:
            title = articles[idx].title[:80] if idx < len(articles) else "?"
            logger.info(f"Event dedup: dropped duplicate event — {title}")

    logger.info(f"Event dedup (embedding): {len(scored_results)} -> {len(kept)}")
    return kept


async def summarize_and_rank(
    articles: list[Article],
    top_n: int = 15,
    batch_size: int = 25,
) -> list[RankedArticle]:
    """
    Two-tier LLM summarization and ranking.

    L1: Cheap model screens all articles (score only, no summaries).
    L2: Strong model deeply analyzes top L1 survivors (full summaries).

    Falls back to keyword ranking when no API key is configured.
    """
    if not _has_api_key():
        provider = LLM_PROVIDER.upper()
        logger.error(f"{provider} API key not set! Cannot summarize.")
        return _fallback_rank(articles, top_n)

    model_info = f"{LLM_PROVIDER}"
    if L2_ENABLED:
        l1_model = OPENAI_MODEL if LLM_PROVIDER == "openai" else ANTHROPIC_MODEL
        l2_model = L2_OPENAI_MODEL if LLM_PROVIDER == "openai" else L2_ANTHROPIC_MODEL
        model_info = f"L1={l1_model}, L2={l2_model}"
    logger.info(f"Two-tier ranking: {model_info}")

    # --- L1: Fast screening ---
    l1_results = await _run_l1_screening(articles, batch_size=batch_size)

    # Sort by L1 score, take top candidates for L2
    l1_results.sort(key=lambda x: x[0], reverse=True)
    l1_pass_count = min(L1_PASS_COUNT, len(l1_results))
    l1_survivors = l1_results[:l1_pass_count]

    logger.info(
        f"L1 screening complete: {len(l1_results)} scored, "
        f"top {l1_pass_count} passed to L2 "
        f"(score range: {l1_survivors[-1][0]:.1f}-{l1_survivors[0][0]:.1f})"
    )

    # Build L2 input
    l2_articles = [articles[idx] for _, idx in l1_survivors]
    l2_orig_indices = [idx for _, idx in l1_survivors]
    l2_l1_scores = [score for score, _ in l1_survivors]

    # --- L2: Deep analysis ---
    l2_results = await _run_l2_deep_analysis(
        l2_articles, l2_orig_indices, l2_l1_scores
    )

    # Sort by L2 score
    l2_results.sort(key=lambda x: x[0], reverse=True)

    # --- Event-level dedup: keep only the best article per event ---
    l2_results = _dedup_by_event(
        l2_results, articles, similarity_threshold=EVENT_DEDUP_THRESHOLD
    )

    # Build final ranked articles
    ranked = []
    for rank, (score, idx, llm_result) in enumerate(l2_results[:top_n], 1):
        if idx < len(articles):
            a = articles[idx]
            ranked.append(RankedArticle(
                title=a.title,
                url=a.url,
                source=a.source,
                language=a.language,
                published=a.published,
                rank=rank,
                relevance_score=score,
                summary=llm_result.get("summary", a.snippet or ""),
                why_important=llm_result.get("why_important", ""),
                topic_matches=a.topic_matches,
            ))

    logger.info(f"Two-tier ranking complete: returning top {len(ranked)} articles")
    return ranked


def _fallback_rank(articles: list[Article], top_n: int) -> list[RankedArticle]:
    """Fallback ranking using keyword scores when no API key is available."""
    from config.topics import relevance_score as calc_score

    scored = [(calc_score(a.topic_matches), a) for a in articles]
    scored.sort(key=lambda x: x[0], reverse=True)

    ranked = []
    for rank, (score, a) in enumerate(scored[:top_n], 1):
        ranked.append(RankedArticle(
            title=a.title,
            url=a.url,
            source=a.source,
            language=a.language,
            published=a.published,
            rank=rank,
            relevance_score=score,
            summary=a.snippet or "(No summary - API key not configured)",
            why_important="Ranked by keyword matching only.",
            topic_matches=a.topic_matches,
        ))
    return ranked
