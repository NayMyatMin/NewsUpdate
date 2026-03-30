#!/usr/bin/env python3
"""
NewsUpdate Agent — Daily AI Safety News Digest
Fetches, deduplicates, filters, summarizes, and ranks the top news
for an AI Safety researcher at Huawei.

Pipeline:
    1. Fetch from 55+ sources (async parallel)
    2. Freshness filter (discard articles older than MAX_ARTICLE_AGE_HOURS)
    3. Deduplicate (URL exact + cross-lingual embedding similarity)
    4. Pre-filter by keyword relevance (cost control gate)
    5. Two-tier LLM ranking:
       L1 — cheap model scores all filtered articles
       L2 — strong model deeply analyzes L1 survivors
    6. Output digest to file + terminal

Usage:
    python main.py                    # Full pipeline
    python main.py --dry-run          # Fetch + filter only (no LLM API call)
    python main.py --top 15           # Return top 15 instead of default
    python main.py --output terminal  # Print to terminal instead of saving file
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone

from config.settings import (
    LLM_PROVIDER,
    FETCH_TIMEOUT_SECONDS,
    MAX_ARTICLES_TO_L1,
    RELEVANCE_KEYWORD_MIN_SCORE,
    TOP_N_OUTPUT,
    L2_ENABLED,
)
from models.article import Digest
from sources.google_news import GoogleNewsFetcher
from sources.rsshub_fetcher import RSSHubFetcher
from sources.rss_fetcher import RSSFetcher
from sources.newsapi_fetcher import NewsAPIFetcher
from sources.wechat_scraper import WeChatScraper
from config.sources import RSS_FEEDS
from processing.deduplicator import deduplicate
from processing.freshness_filter import filter_by_freshness
from processing.relevance_filter import filter_by_relevance
from processing.summarizer import summarize_and_rank
from output.formatter import format_digest_terminal, format_digest_markdown
from output.file_writer import save_digest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("newsupdate")


async def fetch_all_sources() -> list:
    """Fetch from all configured sources in parallel."""
    fetchers = [
        GoogleNewsFetcher(timeout=FETCH_TIMEOUT_SECONDS),
        RSSHubFetcher(timeout=FETCH_TIMEOUT_SECONDS),
        RSSFetcher(feeds=RSS_FEEDS, timeout=FETCH_TIMEOUT_SECONDS),
        NewsAPIFetcher(timeout=FETCH_TIMEOUT_SECONDS),
        WeChatScraper(timeout=15),
    ]

    logger.info(f"Fetching from {len(fetchers)} source groups...")

    results = await asyncio.gather(
        *[f.fetch() for f in fetchers],
        return_exceptions=True,
    )

    all_articles = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Source group {i} failed: {result}")
        else:
            all_articles.extend(result)
            logger.info(f"Source group {i}: {len(result)} articles")

    return all_articles


async def run_pipeline(args: argparse.Namespace) -> None:
    """Execute the full news aggregation pipeline."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info(f"=== NewsUpdate Agent — {today} ===")
    if L2_ENABLED:
        logger.info("Two-tier LLM mode: L1 (screening) + L2 (deep analysis)")

    # Step 1: Fetch
    logger.info("Step 1/5: Fetching from all sources...")
    articles = await fetch_all_sources()
    total_fetched = len(articles)
    logger.info(f"Total fetched: {total_fetched}")

    if not articles:
        logger.warning("No articles fetched! Check your internet connection and source configs.")
        return

    # Step 2: Freshness filter (discard stale articles)
    logger.info("Step 2/6: Filtering by freshness...")
    articles = filter_by_freshness(articles)
    total_after_freshness = len(articles)

    if not articles:
        logger.warning("No articles passed freshness filter! All fetched articles are too old.")
        return

    # Step 3: Deduplicate (embedding-based cross-lingual dedup)
    logger.info("Step 3/6: Deduplicating (cross-lingual)...")
    articles = deduplicate(articles)
    total_after_dedup = len(articles)

    # Step 4: Pre-filter by keyword relevance
    logger.info("Step 4/6: Filtering by relevance...")
    articles = filter_by_relevance(
        articles,
        min_score=RELEVANCE_KEYWORD_MIN_SCORE,
        max_articles=MAX_ARTICLES_TO_L1,
    )
    total_after_filter = len(articles)

    if not articles:
        logger.warning("No articles passed relevance filter! Consider lowering RELEVANCE_KEYWORD_MIN_SCORE.")
        return

    # Step 5: Two-tier LLM ranking
    top_n = args.top if hasattr(args, "top") else TOP_N_OUTPUT

    if args.dry_run:
        logger.info("Step 5/6: DRY RUN — skipping LLM API calls")
        from processing.summarizer import _fallback_rank
        ranked = _fallback_rank(articles, top_n)
    else:
        logger.info(f"Step 5/6: Two-tier ranking {len(articles)} articles with {LLM_PROVIDER}...")
        ranked = await summarize_and_rank(articles, top_n=top_n)

    # Step 6: Output
    logger.info("Step 6/6: Generating digest...")
    digest = Digest(
        date=today,
        generated_at=datetime.now(timezone.utc),
        total_fetched=total_fetched,
        total_after_freshness=total_after_freshness,
        total_after_dedup=total_after_dedup,
        total_after_filter=total_after_filter,
        top_articles=ranked,
    )

    # Always save to file
    filepath = save_digest(digest)
    logger.info(f"Digest saved to: {filepath}")

    # Terminal output
    print(format_digest_terminal(digest))

    logger.info("=== Done ===")


def main():
    parser = argparse.ArgumentParser(
        description="NewsUpdate Agent — Daily AI Safety News Digest"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and filter only, skip LLM summarization",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=TOP_N_OUTPUT,
        help=f"Number of top articles to include (default: {TOP_N_OUTPUT})",
    )
    parser.add_argument(
        "--output",
        choices=["file", "terminal"],
        default="file",
        help="Output mode: save to file or print to terminal only",
    )
    args = parser.parse_args()

    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
