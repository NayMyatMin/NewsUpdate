#!/usr/bin/env python3
"""
Generate an LLM-powered weekly trend analysis from daily digest files.

Uses the project's L2 (strong) model to produce a structured weekly briefing
with executive summary, key trends, top stories, and a watch list.
Falls back to a simple top-5 extraction if the LLM call fails or no API key
is configured.

Usage:
    python scripts/generate_weekly_summary.py digests/2026-03-23_to_2026-03-29/
"""

import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so config/processing imports work
# when the script is invoked directly.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def parse_articles_from_digest(filepath: Path) -> list[dict]:
    """Extract ranked articles from a daily digest markdown file."""
    text = filepath.read_text(encoding="utf-8")
    articles = []

    # Split by article sections: ## 1. [Title](url)
    pattern = re.compile(
        r"^## \d+\.\s+\[(.+?)\]\((.+?)\)\s*\n"
        r"\*\*Source:\*\*\s*(.+?)\s*\|\s*(.+?)\s*\|\s*\*\*Relevance:\*\*\s*([\d.]+)/10\s*\n"
        r"\n>\s*(.+?)\n"
        r"(?:\n\*\*Why it matters:\*\*\s*(.+?)\n)?",
        re.MULTILINE,
    )

    for m in pattern.finditer(text):
        articles.append({
            "title": m.group(1),
            "url": m.group(2),
            "source": m.group(3).strip(),
            "date": m.group(4).strip(),
            "score": float(m.group(5)),
            "summary": m.group(6).strip(),
            "why_important": m.group(7).strip() if m.group(7) else "",
            "digest_date": filepath.stem,  # e.g. "2026-03-28"
        })

    return articles


def deduplicate_by_title(articles: list[dict]) -> list[dict]:
    """Remove articles covering the same story (similar titles)."""
    seen_titles = []
    unique = []
    for article in articles:
        title_lower = article["title"].lower()
        # Check if this title is too similar to one we've already kept
        is_dup = False
        for seen in seen_titles:
            # Simple word overlap check
            words_a = set(title_lower.split())
            words_b = set(seen.split())
            overlap = len(words_a & words_b) / max(len(words_a | words_b), 1)
            if overlap > 0.6:
                is_dup = True
                break
        if not is_dup:
            unique.append(article)
            seen_titles.append(title_lower)
    return unique


# ---------------------------------------------------------------------------
# Weekly trend analysis prompt
# ---------------------------------------------------------------------------
_WEEKLY_SYSTEM_PROMPT = """You are a senior AI-safety intelligence analyst preparing a weekly \
briefing for an AI Safety researcher at Huawei.

Your audience is technically sophisticated and cares about:
- AI safety, alignment, adversarial robustness, red-teaming
- AI security (prompt injection, jailbreaks, supply-chain attacks)
- Frontier model releases and capability jumps
- AI governance and regulation (China and international)
- Huawei ecosystem (HarmonyOS, Ascend, MindSpore, Kunpeng)
- Geopolitical AI competition (US-China, chip export controls)
- Cybersecurity incidents, zero-days, vulnerability disclosures
- Open-source AI models (DeepSeek, Qwen, LLaMA, etc.)

Write in a direct, analytical style. Be specific — cite article titles when \
referencing evidence. Do NOT invent information beyond what is in the provided \
articles."""

_WEEKLY_USER_PROMPT_TEMPLATE = """Below are {count} deduplicated articles from the week of \
{week_start} to {week_end}, sorted by relevance score (highest first). Each article \
includes its title, source, date, relevance score, summary, and a note on why it matters.

Produce a structured weekly briefing in **Markdown** with EXACTLY these four sections:

## Executive Summary
3-4 sentences on the week's most significant developments and their overall implications.

## Key Trends
3-5 emerging patterns or themes you observe across this week's articles. For each trend, \
give a short heading, a 2-3 sentence explanation, and reference the specific articles \
(by title) that support it.

## Top 5 Stories
The 5 most important individual stories. For each, include:
- The article title as a markdown link (use the URL from the data)
- Source and date
- A 2-3 sentence analysis of why this story is the most important
- Relevance score

## Watch List
2-3 developing situations to monitor next week, based on the trajectories visible in \
this week's coverage. For each, explain briefly what to watch for.

---

Articles JSON:
```json
{articles_json}
```"""


def generate_llm_summary(articles: list[dict], week_start: str, week_end: str) -> str:
    """Send weekly articles to the LLM and return a structured markdown briefing.

    Uses the project's L2 (strong) model since this runs only once per week.
    Raises on any error so the caller can fall back to the simple approach.
    """
    from config.settings import (
        LLM_PROVIDER,
        ANTHROPIC_API_KEY,
        OPENAI_API_KEY,
        L2_OPENAI_MODEL,
        L2_ANTHROPIC_MODEL,
    )
    from processing.summarizer import _call_llm

    # Verify an API key is available
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        raise RuntimeError("No OpenAI API key configured")
    if LLM_PROVIDER != "openai" and not ANTHROPIC_API_KEY:
        raise RuntimeError("No Anthropic API key configured")

    # Pick the L2 (strong) model
    model = L2_OPENAI_MODEL if LLM_PROVIDER == "openai" else L2_ANTHROPIC_MODEL

    # Build the articles payload — keep the fields the prompt references
    articles_payload = []
    for i, a in enumerate(articles):
        articles_payload.append({
            "index": i,
            "title": a["title"],
            "url": a["url"],
            "source": a["source"],
            "date": a["date"],
            "relevance_score": a["score"],
            "summary": a["summary"],
            "why_important": a["why_important"],
            "digest_date": a["digest_date"],
        })

    articles_json = json.dumps(articles_payload, ensure_ascii=False, indent=2)

    user_prompt = _WEEKLY_USER_PROMPT_TEMPLATE.format(
        count=len(articles),
        week_start=week_start,
        week_end=week_end,
        articles_json=articles_json,
    )

    logger.info(
        "Requesting weekly trend analysis from %s model %s (%d articles)",
        LLM_PROVIDER, model, len(articles),
    )

    response = _call_llm(
        _WEEKLY_SYSTEM_PROMPT,
        user_prompt,
        model=model,
        max_tokens=8192,
    )

    return response


def _generate_simple_summary(
    top5: list[dict],
    daily_file_count: int,
    total_article_count: int,
    week_start: str,
    week_end: str,
) -> str:
    """Fallback: produce the original simple top-5 markdown (no LLM)."""
    lines = [
        f"# Weekly Summary — {week_start} to {week_end}",
        "",
        f"*Top 5 stories from {daily_file_count} daily digests "
        f"({total_article_count} total articles reviewed)*",
        "",
        "---",
        "",
    ]

    for i, article in enumerate(top5, 1):
        lines.append(f"## {i}. [{article['title']}]({article['url']})")
        lines.append(
            f"**Source:** {article['source']} | {article['date']} "
            f"| **Relevance:** {article['score']}/10 "
            f"| *From {article['digest_date']} digest*"
        )
        lines.append("")
        lines.append(f"> {article['summary']}")
        lines.append("")
        if article["why_important"]:
            lines.append(f"**Why it matters:** {article['why_important']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.append(
        "*Generated by NewsUpdate Agent — Weekly Summary (fallback, no LLM)*"
    )
    lines.append("")
    return "\n".join(lines)


def generate_summary(week_dir: Path) -> None:
    """Generate weekly-summary.md in the given week directory.

    Tries LLM-powered trend analysis first; falls back to the simple
    top-5 extraction if the LLM call fails or no API key is available.
    """
    # Collect all daily digests
    daily_files = sorted(week_dir.glob("????-??-??.md"))
    if not daily_files:
        print(f"No daily digests found in {week_dir}")
        return

    # Parse all articles from all daily digests
    all_articles = []
    for f in daily_files:
        all_articles.extend(parse_articles_from_digest(f))

    if not all_articles:
        print(f"No articles parsed from {week_dir}")
        return

    # Sort by relevance score (descending), deduplicate similar stories
    all_articles.sort(key=lambda a: a["score"], reverse=True)
    unique_articles = deduplicate_by_title(all_articles)

    # Determine week range from folder name
    folder_name = week_dir.name  # e.g. "2026-03-23_to_2026-03-29"
    parts = folder_name.split("_to_")
    week_start = parts[0]
    week_end = parts[1] if len(parts) > 1 else "unknown"

    # --- Try LLM-powered weekly trend analysis ---
    markdown: str | None = None
    try:
        llm_body = generate_llm_summary(unique_articles, week_start, week_end)

        # Wrap the LLM output with a header and footer
        header_lines = [
            f"# Weekly Trend Analysis — {week_start} to {week_end}",
            "",
            f"*AI-generated briefing from {len(daily_files)} daily digests "
            f"({len(all_articles)} total articles, "
            f"{len(unique_articles)} after deduplication)*",
            "",
            "---",
            "",
        ]
        footer_lines = [
            "",
            "---",
            "",
            "*Generated by NewsUpdate Agent — LLM Weekly Trend Analysis*",
            "",
        ]
        markdown = "\n".join(header_lines) + llm_body + "\n".join(footer_lines)
        print("LLM weekly trend analysis generated successfully.")

    except Exception as exc:
        logger.warning("LLM weekly summary failed, falling back to simple top-5: %s", exc)
        print(f"LLM analysis failed ({exc}), falling back to simple top-5 summary.")

    # --- Fallback: simple top-5 ---
    if markdown is None:
        top5 = unique_articles[:5]
        markdown = _generate_simple_summary(
            top5, len(daily_files), len(all_articles), week_start, week_end
        )

    output_path = week_dir / "weekly-summary.md"
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Generated {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_weekly_summary.py <week_folder>")
        sys.exit(1)

    week_dir = Path(sys.argv[1])
    if not week_dir.is_dir():
        print(f"Not a directory: {week_dir}")
        sys.exit(1)

    generate_summary(week_dir)
