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
    MAX_FULLTEXT_LENGTH,
)
from models.article import Article, RankedArticle, DIGEST_SECTIONS
from processing.content_fetcher import fetch_full_text
from processing.deduplicator import _get_embeddings, _cosine_similarity

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a tech news analyst for an AI Safety researcher at Huawei.
Your job is to evaluate news articles focused on AI security, AI safety, and related threats.

The researcher primarily cares about:
- AI safety, alignment, and responsible AI
- AI security (adversarial attacks, prompt injection, jailbreaking, red teaming)
- Cybersecurity incidents affecting AI systems or infrastructure
- AI agents: safety failures, frameworks, OS-level integrations
- AI governance, regulation, and policy (China and international)
- Research: safety evaluation, benchmarks, red-teaming methods, alignment techniques

The researcher is LESS interested in:
- General industry moves (chip launches, business strategy, earnings) UNLESS they
  directly relate to AI safety or security
- General tech news without an AI safety/security angle

Be especially attentive to:
1. Breaking security incidents and active exploits (highest urgency)
2. Breaking developments that shift the AI safety landscape
3. New vulnerabilities or attack methods (on AI systems or general infra)
4. AI agent safety failures and new agent platform features from OS vendors
5. Regulatory changes in China or internationally
6. New safety/security research, benchmarks, and evaluation methods"""

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
2. section: Categorize into EXACTLY ONE of these sections:
   - "threats_incidents": Real-world active attacks, data breaches, ransomware, jailbreaks, prompt
     injection exploits, CVEs, safety failures, vulnerability disclosures, security incidents.
     ONLY for real-world news/incidents, NOT academic papers.
   - "ai_security_industry": AI safety/security announcements, tools, features, guardrail releases
     from major companies (Google, OpenAI, Meta, Anthropic, Huawei, Microsoft, Alibaba, ByteDance,
     DeepSeek, etc.). Only for real-world product/company news, NOT academic papers.
   - "ai_agents_os": AI agent features from OS platforms (Apple/iOS, Android, Windows, HarmonyOS),
     agent frameworks, platform-level agent permission/control systems, agentic safety features.
     Only for real-world product/platform news, NOT academic papers.
   - "research_regulation": Academic papers (ArXiv, conferences), safety benchmarks, evaluation
     methods, red-teaming research, AI governance, regulation, policy changes, standards.
     ALL academic/research papers MUST go here regardless of topic.
3. summary (2-3 sentences): Key facts, technical details, and implications
4. why_important (1 sentence): Why this specifically matters for AI safety research at Huawei

Scoring guide:
- 9-10: Active security incident, critical AI safety breakthrough, critical zero-day
- 7-8: Significant AI safety/security advance, new vulnerability/CVE, important regulatory action
- 5-6: Notable AI safety-adjacent news, interesting research, minor updates
- 0-4: Not directly relevant to AI safety/security (score low so it gets filtered out)

Articles:
{articles_json}

Respond ONLY with a valid JSON array of exactly {count} elements. Each element must have:
"index", "relevance_score", "section", "summary", "why_important"

Example: [{{"index": 0, "relevance_score": 8.5, "section": "threats_incidents", "summary": "...", "why_important": "..."}}]"""


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

    # L2 gets full-text content for deeper analysis
    articles_json = _format_articles_for_prompt(articles, max_snippet=MAX_FULLTEXT_LENGTH)

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


def _is_research_source(article: Article) -> bool:
    """Check if an article comes from a research/academic source (e.g., ArXiv)."""
    source_lower = article.source.lower()
    url_lower = article.url.lower()
    return "arxiv" in source_lower or "arxiv.org" in url_lower


def _distribute_across_sections(
    scored_results: list[tuple[float, int, dict]],
    articles: list[Article],
    top_n: int,
) -> list[RankedArticle]:
    """
    Distribute top articles across digest sections.

    Rules:
    - Research/academic sources (ArXiv) always go to research_regulation
    - Soft minimums per section are filled first
    - Hard max per section is enforced (e.g., research capped at 5)
    - Remaining slots filled by score
    - Total output is top_n articles
    """
    valid_sections = set(DIGEST_SECTIONS.keys())

    # Group results by section, forcing research sources into research_regulation
    by_section: dict[str, list[tuple[float, int, dict]]] = {s: [] for s in valid_sections}
    for score, idx, llm_result in scored_results:
        if idx < len(articles) and _is_research_source(articles[idx]):
            section = "research_regulation"
        else:
            section = llm_result.get("section", "")
            if section not in valid_sections:
                section = "research_regulation"
        by_section[section].append((score, idx, llm_result))

    # Sort each section by score
    for section in by_section:
        by_section[section].sort(key=lambda x: x[0], reverse=True)

    # Enforce hard max per section (trim before distribution)
    for section_id, section_def in DIGEST_SECTIONS.items():
        max_count = section_def.get("max_articles")
        if max_count is not None and len(by_section[section_id]) > max_count:
            by_section[section_id] = by_section[section_id][:max_count]

    # Phase 1: Fill soft minimums for each section
    selected: list[tuple[float, int, dict, str]] = []  # (score, idx, llm_result, section)
    remaining: list[tuple[float, int, dict, str]] = []

    for section_id, section_def in DIGEST_SECTIONS.items():
        min_count = section_def["min_articles"]
        max_count = section_def.get("max_articles")
        section_items = by_section[section_id]
        for i, item in enumerate(section_items):
            if i < min_count:
                selected.append((*item, section_id))
            else:
                remaining.append((*item, section_id))

    # Phase 2: Fill remaining slots by score, respecting hard max
    slots_left = top_n - len(selected)
    remaining.sort(key=lambda x: x[0], reverse=True)

    # Count how many are already selected per section
    section_counts: dict[str, int] = {}
    for _, _, _, sec in selected:
        section_counts[sec] = section_counts.get(sec, 0) + 1

    for item in remaining:
        if slots_left <= 0:
            break
        sec = item[3]
        max_count = DIGEST_SECTIONS[sec].get("max_articles")
        if max_count is not None and section_counts.get(sec, 0) >= max_count:
            continue
        selected.append(item)
        section_counts[sec] = section_counts.get(sec, 0) + 1
        slots_left -= 1

    # Build RankedArticle list, ordered by section then by score within section
    ranked = []
    rank = 1
    for section_id in DIGEST_SECTIONS:
        section_articles = [
            (score, idx, llm_result) for score, idx, llm_result, sec in selected
            if sec == section_id
        ]
        section_articles.sort(key=lambda x: x[0], reverse=True)
        for score, idx, llm_result in section_articles:
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
                    section=section_id,
                    topic_matches=a.topic_matches,
                ))
                rank += 1

    section_counts = {}
    for a in ranked:
        section_counts[a.section] = section_counts.get(a.section, 0) + 1
    logger.info(f"Section distribution: {section_counts}")

    return ranked


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

    # --- Fetch full-text content for L2 candidates ---
    try:
        full_texts = await fetch_full_text(l2_articles)
        enriched_count = 0
        for article in l2_articles:
            if article.url in full_texts:
                article.snippet = full_texts[article.url]
                enriched_count += 1
        logger.info(
            f"Full-text fetch: {enriched_count}/{len(l2_articles)} articles enriched, "
            f"{len(l2_articles) - enriched_count} using original snippet"
        )
    except Exception as e:
        logger.warning(f"Full-text fetch failed, using original snippets: {e}")

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

    # Build sectioned ranked articles (15 total, disproportionate across sections)
    ranked = _distribute_across_sections(l2_results, articles, top_n)

    logger.info(f"Two-tier ranking complete: returning {len(ranked)} articles across sections")
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
            section="research_regulation",  # Default section for fallback
            topic_matches=a.topic_matches,
        ))
    return ranked
