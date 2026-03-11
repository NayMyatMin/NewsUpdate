import json
import logging

from config.settings import (
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_BASE_URL,
)
from models.article import Article, RankedArticle

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

BATCH_PROMPT_TEMPLATE = """Evaluate the following {count} news articles from the past 24 hours.

For each article, provide:
1. relevance_score (0.0-10.0): How important for a tech-savvy AI safety researcher at Huawei
2. summary (2-3 sentences): Key facts and implications
3. why_important (1 sentence): Why this matters

Scoring guide:
- 9-10: Active security incident, critical AI safety breakthrough, major Huawei news, or critical zero-day
- 7-8: Significant AI advance, new vulnerability/CVE, important regulatory action, major breach
- 5-6: Notable tech industry news, cloud/infra updates, interesting research
- 3-4: Minor tech updates, tangential news
- 0-2: Not relevant

Articles:
{articles_json}

Respond ONLY with a valid JSON array. Each element must have these exact keys:
"index", "relevance_score", "summary", "why_important"

Example format:
[{{"index": 0, "relevance_score": 8.5, "summary": "...", "why_important": "..."}}]"""


def _format_articles_for_prompt(articles: list[Article]) -> str:
    """Format articles as a numbered JSON list for the prompt."""
    items = []
    for i, a in enumerate(articles):
        items.append({
            "index": i,
            "title": a.title,
            "source": a.source,
            "language": a.language,
            "snippet": (a.snippet or "")[:300],
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


def _call_anthropic(system: str, user_prompt: str) -> str:
    """Call Anthropic Claude API and return response text."""
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text.strip()


def _call_openai(system: str, user_prompt: str) -> str:
    """Call OpenAI (or compatible) API and return response text."""
    import openai

    kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL

    client = openai.OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def _call_llm(system: str, user_prompt: str) -> str:
    """Route to the configured LLM provider."""
    if LLM_PROVIDER == "openai":
        return _call_openai(system, user_prompt)
    else:
        return _call_anthropic(system, user_prompt)


def _has_api_key() -> bool:
    """Check if the configured provider has an API key."""
    if LLM_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    return bool(ANTHROPIC_API_KEY)


async def summarize_and_rank(
    articles: list[Article],
    top_n: int = 10,
    batch_size: int = 25,
) -> list[RankedArticle]:
    """
    Send articles to LLM for summarization and ranking.
    Supports both Anthropic and OpenAI providers.
    Processes in batches to stay within token limits.
    Returns top_n ranked articles.
    """
    if not _has_api_key():
        provider = LLM_PROVIDER.upper()
        logger.error(f"{provider} API key not set! Cannot summarize.")
        return _fallback_rank(articles, top_n)

    model = OPENAI_MODEL if LLM_PROVIDER == "openai" else ANTHROPIC_MODEL
    logger.info(f"Using LLM provider: {LLM_PROVIDER} (model: {model})")

    all_scored: list[tuple[float, int, dict]] = []

    # Process in batches
    for batch_start in range(0, len(articles), batch_size):
        batch = articles[batch_start : batch_start + batch_size]
        articles_json = _format_articles_for_prompt(batch)

        prompt = BATCH_PROMPT_TEMPLATE.format(
            count=len(batch),
            articles_json=articles_json,
        )

        try:
            response_text = _call_llm(SYSTEM_PROMPT, prompt)
            response_text = _strip_code_fences(response_text)
            results = json.loads(response_text)

            for item in results:
                idx = item.get("index", 0)
                global_idx = batch_start + idx
                score = float(item.get("relevance_score", 0))
                all_scored.append((score, global_idx, item))

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            for i in range(len(batch)):
                all_scored.append((0, batch_start + i, {}))
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            for i in range(len(batch)):
                all_scored.append((0, batch_start + i, {}))

    # Sort by relevance score descending
    all_scored.sort(key=lambda x: x[0], reverse=True)

    # Build top-N ranked articles
    ranked = []
    for rank, (score, idx, llm_result) in enumerate(all_scored[:top_n], 1):
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

    logger.info(f"Summarized {len(articles)} articles, returning top {len(ranked)}")
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
