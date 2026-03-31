# NewsUpdate Agent

Daily AI safety news digest powered by LLM analysis. Fetches 1,800+ articles from 110+ sources (international + Chinese), filters by freshness, deduplicates, and uses a two-tier LLM pipeline to rank and summarize the top 15 articles — organized into thematic sections for an AI Safety researcher.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and add your OpenAI API key

# 3. Run
python main.py
```

## Usage

```bash
python main.py                    # Full run — summarize with LLM, save to digests/
python main.py --output terminal  # Print to terminal only, don't save file
python main.py --dry-run          # Fetch + keyword ranking only (no LLM cost)
python main.py --top 20           # Top 20 instead of default 15
python main.py --dry-run --top 5  # Quick preview, no API call
```

Output is saved to `digests/YYYY-MM-DD.md`.

## Digest Sections

The digest is organized into 4 thematic sections (in this order):

| Section | What goes in it | Limits |
|---|---|---|
| **Threats & Incidents** | Active attacks, breaches, jailbreaks, CVEs, safety failures | Min 2 |
| **AI Security from Major Players** | Safety/security announcements, tools, guardrails from Google, OpenAI, Meta, etc. | Min 2 |
| **AI Agents & OS Integration** | Agent features from Apple/Android/Windows/HarmonyOS, agent frameworks | Shows "No significant developments" if empty |
| **Research & Regulation** | Papers, benchmarks, standards, governance, policy | Min 2, Max 5 |

- **Total: 15 articles**, distributed by importance across sections
- Academic/ArXiv papers are always routed to Research & Regulation (never in Threats or Industry)
- Only real-world news appears in Threats & Incidents and AI Security sections

## Configuration

All config lives in `.env` (or GitHub Secrets for CI):

```bash
# LLM provider: "openai" (default) or "anthropic"
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o-mini          # L1 screening model (fast, cheap)
L2_OPENAI_MODEL=gpt-4o            # L2 deep analysis model (stronger)
L2_ENABLED=true                   # Set false to use L1 model for everything

# Or use any OpenAI-compatible API (Ollama, vLLM, Azure, etc.)
# OPENAI_BASE_URL=http://localhost:11434/v1

# Anthropic (if LLM_PROVIDER=anthropic)
# ANTHROPIC_API_KEY=sk-ant-xxxxx
# ANTHROPIC_MODEL=claude-haiku-4-5-20251001
# L2_ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Embedding model for cross-lingual deduplication
EMBEDDING_MODEL=text-embedding-3-small

# RSSHub (auto-hosted in GitHub Actions, fallback to public instances locally)
# RSSHUB_BASE_URL=http://localhost:1200

# Optional: NewsAPI.org for extra international coverage
# NEWSAPI_KEY=xxxxx

# Pipeline tuning
# MAX_ARTICLE_AGE_HOURS=48         # Discard articles older than this (default: 48)
# MAX_FULLTEXT_LENGTH=2000         # Max chars fetched for L2 full-text enrichment
```

## How It Works

```
Fetch (110+ source configs, async)
  → 1,800+ raw articles
    → Freshness filter (drop articles older than 48h)
      → ~1,700 fresh
        → Deduplicate (URL + cross-lingual embeddings)
          → ~1,500 unique
            → Keyword relevance filter (17 topic clusters)
              → Top 80 candidates
                → L1 LLM screening (fast model)
                  → Top 25 finalists
                    → Full-text content fetch (enrich L2 input)
                      → L2 LLM deep analysis + section categorization
                        → Top 15 digest (4 thematic sections)
```

**Pipeline stages (6 steps):**

| Stage | What it does | Cost |
|---|---|---|
| Fetch | Async RSS/scraping from all sources | Free |
| Freshness | Drop articles older than 48h | Free |
| Dedup | URL + cross-lingual embedding similarity | ~$0.01/day |
| Filter | Keyword matching across 17 topic clusters | Free |
| L1 Screen | Fast LLM scores and filters top candidates | ~$0.02/day |
| Full-text | Fetch article body for L2 candidates (up to 2000 chars) | Free |
| L2 Rank | Stronger LLM deep-analyzes, categorizes into sections, and ranks | ~$0.05/day |
| Output | Sectioned Markdown file + terminal display | Free |

## Sources

### International (English)

**AI & ML:**
TechCrunch AI, Wired AI, MIT Tech Review, The Verge AI, ArXiv (cs.AI, cs.CR, cs.CL), Google AI Blog, OpenAI Blog, Hugging Face Blog, DeepMind Blog, Meta Engineering ML, Apple ML Blog, Microsoft AI Blog, Lil'Log, NLP Newsletter, Import AI

**Cybersecurity & Infosec:**
BleepingComputer, The Hacker News, Dark Reading, SecurityWeek, Krebs on Security, Schneier on Security, CISA, NIST NVD, Cisco Talos, Mandiant, Securelist (Kaspersky), Unit 42 (Palo Alto), SentinelOne Labs, Cloudflare Blog, PortSwigger Research, Google Project Zero

**General Tech:**
Hacker News (YC), Lobsters, InfoQ, GitHub Blog, BBC Tech, NYT Tech, Ars Technica

**Cloud & Infrastructure:**
AWS Blog, Google Cloud Blog, Azure Blog, Kubernetes Blog, MS DevOps Blog

**Dev:**
Go Blog, Rust Blog

### Chinese (中文)

**Google News (12 queries):**
AI安全, 大模型, 华为, 芯片, AI监管, 网络安全, 安全漏洞, 信息安全, 云计算, 量子计算, 自动驾驶, 科技公司

**WeChat (16 queries via Sogou):**
AI安全, 大模型安全, 人工智能治理, 华为AI, AI智能体, 大语言模型, AI芯片, 深度伪造, 网络安全事件, 数据泄露, 勒索软件攻击, 安全漏洞, 云计算, 量子计算, 自动驾驶, 科技新闻

**Direct feeds:**
Seebug Paper, Xianzi (先知社区), InfoQ China

**RSSHub (13 routes via self-hosted container in CI):**
CLS Telegraph (财联社), 36Kr, The Paper (澎湃), Zhihu, V2EX, Jiqizhixin (机器之心), Leiphone (雷锋网), Anquanke (安全客), Bilibili Tech, Weibo

> In GitHub Actions, RSSHub runs as a service container (`diygod/rsshub`) for reliable, unthrottled access. Locally, it falls back to public instances.

## Topic Clusters (17)

| Priority | Topics |
|---|---|
| High (3.0) | AI Safety & Alignment, AI Security & Attacks, Huawei Ecosystem |
| Medium-High (2.5) | LLMs, AI Agents, Cybersecurity & Incidents, AI Governance |
| Medium (2.0) | Frontier Models, Mobile/Telecom, Geopolitical AI, AI in Cybersecurity, Cloud & Infra, Privacy & Data |
| Standard (1.5) | Software & Dev Tools, Blockchain, Quantum Computing, Robotics & Hardware, Big Tech Business |

## Weekly Trend Analysis

At the end of each week, an LLM-powered trend analysis is generated from all daily digests. It includes:

- **Executive Summary** — the week's most significant developments
- **Key Trends** — emerging patterns with article references
- **Top 5 Stories** — deepest analysis of the most important stories
- **Watch List** — developing situations to monitor next week

Falls back to a simple top-5 extraction if the LLM call fails. Output: `digests/<week_folder>/weekly-summary.md`.

## Cost

| Setup | L1 Model | L2 Model | Daily Cost | Monthly Cost |
|---|---|---|---|---|
| Budget | gpt-4o-mini | gpt-4o-mini | ~$0.04 | ~$1.20 |
| Recommended | gpt-4o-mini | gpt-4o | ~$0.08 | ~$2.50 |
| Premium | gpt-5-mini | gpt-5-mini | ~$0.06 | ~$1.80 |
| Anthropic | claude-haiku-4-5 | claude-sonnet-4 | ~$0.10 | ~$3 |
| Local (Ollama) | any | any | $0 | $0 |

*Costs include embedding API calls for cross-lingual deduplication and full-text fetching.*

## GitHub Actions (Automated Daily Digest)

The included workflow runs the pipeline daily at 01:00 UTC (09:00 SGT) with a self-hosted RSSHub service container and commits the digest automatically.

**Setup:**
1. Go to **Settings → Secrets and variables → Actions**
2. Add required secrets:
   - `LLM_PROVIDER` → `openai`
   - `OPENAI_API_KEY` → your API key
3. Optionally set `OPENAI_MODEL` and `L2_OPENAI_MODEL` to customize models
4. Go to **Actions → Daily News Digest → Run workflow** to trigger manually

## Run as Daily Cron Job (Local)

```bash
# Edit crontab
crontab -e

# Run every day at 7:00 AM UTC
0 7 * * * cd /path/to/newsupdate && python3 main.py >> logs/cron.log 2>&1
```

## Project Structure

```
newsupdate/
├── main.py                         # Entry point — 6-step pipeline orchestrator
├── .env                            # API keys and configuration
├── requirements.txt                # Python dependencies
├── config/
│   ├── settings.py                 # API keys, model config, thresholds
│   ├── topics.py                   # 17 topic clusters with EN/ZH keywords
│   └── sources.py                  # 110+ source definitions (RSS, Google News, RSSHub, WeChat)
├── sources/
│   ├── rss_fetcher.py              # Async RSS/Atom feed parser
│   ├── google_news.py              # Google News RSS search (28 queries)
│   ├── rsshub_fetcher.py           # RSSHub sources with service container + fallback instances
│   ├── newsapi_fetcher.py          # NewsAPI.org (optional)
│   └── wechat_scraper.py           # WeChat articles via Sogou search
├── processing/
│   ├── freshness_filter.py         # Drop articles older than MAX_ARTICLE_AGE_HOURS
│   ├── deduplicator.py             # URL + cross-lingual embedding dedup
│   ├── relevance_filter.py         # Keyword-based pre-filter
│   ├── content_fetcher.py          # Full-text fetcher for L2 candidate enrichment
│   └── summarizer.py               # Two-tier LLM ranking + section categorization
├── output/
│   ├── formatter.py                # Sectioned Markdown + terminal formatters
│   └── file_writer.py              # Save digest to file
├── models/
│   └── article.py                  # Pydantic data models + digest section definitions
├── scripts/
│   ├── generate_weekly_summary.py  # LLM-powered weekly trend analysis
│   └── organize_digests.sh         # Archive completed weeks into folders
├── digests/                        # Daily digest output files (organized by week)
├── tests/                          # Test suite
└── logs/                           # Run logs
```

## Adding Sources

Edit `config/sources.py`:

```python
# Add an RSS feed
RSS_FEEDS.append({
    "url": "https://example.com/feed.xml",
    "source": "Example Blog",
    "lang": "en",  # or "zh"
})

# Add a Google News query
GOOGLE_NEWS_QUERIES.append({
    "query": "your search terms",
    "lang": "en",  # or "zh"
})

# Add a WeChat search query
WECHAT_SEARCH_QUERIES.append("搜索关键词")
```

## Adding Topics

Edit `config/topics.py`:

```python
TOPICS["new_topic"] = {
    "label": "New Topic",
    "weight": 2.0,  # 1.5-3.0, higher = more important
    "keywords_en": ["keyword1", "keyword2"],
    "keywords_zh": ["关键词1", "关键词2"],
}
```

## Using Local Models (Ollama)

```bash
# Start Ollama
ollama serve
ollama pull llama3.1

# Configure .env
LLM_PROVIDER=openai
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama3.1
OPENAI_BASE_URL=http://localhost:11434/v1
```

## License

Internal use.
