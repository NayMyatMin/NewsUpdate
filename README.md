# NewsUpdate Agent

Daily tech news digest powered by AI. Fetches 1,500+ articles from 110 sources (international + Chinese), deduplicates, filters by relevance, and uses an LLM to rank and summarize the top 15 things you need to know.

Built for staying current on AI, cybersecurity, LLMs, AI agents, cloud, hardware, and general tech — from both international and Chinese domestic sources.

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

# RSSHub base URL (default: https://rsshub.app, auto-fallback on 403)
# RSSHUB_BASE_URL=https://rsshub.app

# Optional: NewsAPI.org for extra international coverage
# NEWSAPI_KEY=xxxxx
```

## How It Works

```
Fetch (110 source configs, async)
  → 1,500+ raw articles
    → Deduplicate (URL + cross-lingual embeddings)
      → ~1,300 unique
        → Keyword relevance filter (17 topic clusters)
          → Top 80 candidates
            → L1 LLM screening (fast model)
              → Top 25 finalists
                → L2 LLM deep analysis (8K token budget, backfill guarantee)
                  → Top 15 digest (always 15 — never truncated)
```

**Pipeline stages:**

| Stage | What it does | Cost |
|---|---|---|
| Fetch | Async RSS/scraping from all sources | Free |
| Dedup | URL + cross-lingual embedding similarity | ~$0.01/day |
| Filter | Keyword matching across 17 topic clusters | Free |
| L1 Screen | Fast LLM scores and filters top candidates | ~$0.02/day |
| L2 Rank | Stronger LLM deep-analyzes and ranks top articles | ~$0.05/day |
| Output | Markdown file + terminal display | Free |

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

**RSSHub (14 routes, auto-fallback across 4 public instances):**
CLS Telegraph (财联社), 36Kr, The Paper (澎湃), Zhihu, V2EX, Jiqizhixin (机器之心), Leiphone (雷锋网), Anquanke (安全客), Bilibili Tech, Weibo

> RSSHub routes automatically try fallback instances (`hub.slarker.me`, `rsshub.qufy.me`, `rsshub.wkfg.me`, `rss.shab.fun`) when the primary instance returns 403 or is unreachable. Failed routes log a single warning instead of per-attempt noise.

## Topic Clusters (17)

| Priority | Topics |
|---|---|
| High (3.0) | AI Safety & Alignment, AI Security & Attacks, Huawei Ecosystem |
| Medium-High (2.5) | LLMs, AI Agents, Cybersecurity & Incidents, AI Governance |
| Medium (2.0) | Frontier Models, Mobile/Telecom, Geopolitical AI, AI in Cybersecurity, Cloud & Infra, Privacy & Data |
| Standard (1.5) | Software & Dev Tools, Blockchain, Quantum Computing, Robotics & Hardware, Big Tech Business |

## Cost

| Setup | L1 Model | L2 Model | Daily Cost | Monthly Cost |
|---|---|---|---|---|
| Budget | gpt-4o-mini | gpt-4o-mini | ~$0.04 | ~$1.20 |
| Recommended | gpt-4o-mini | gpt-4o | ~$0.08 | ~$2.50 |
| Premium | gpt-5-mini | gpt-5-mini | ~$0.06 | ~$1.80 |
| Anthropic | claude-haiku-4-5 | claude-sonnet-4 | ~$0.10 | ~$3 |
| Local (Ollama) | any | any | $0 | $0 |

*Costs include embedding API calls for cross-lingual deduplication.*

## GitHub Actions (Automated Daily Digest)

The included workflow runs the pipeline daily at 07:00 UTC and commits the digest automatically.

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
├── main.py                         # Entry point — pipeline orchestrator
├── .env                            # API keys and configuration
├── requirements.txt                # Python dependencies
├── config/
│   ├── settings.py                 # API keys, model config, thresholds
│   ├── topics.py                   # 17 topic clusters with EN/ZH keywords
│   └── sources.py                  # 110 source definitions (RSS, Google News, RSSHub, WeChat)
├── sources/
│   ├── rss_fetcher.py              # Async RSS/Atom feed parser
│   ├── google_news.py              # Google News RSS search (28 queries)
│   ├── rsshub_fetcher.py           # RSSHub sources with auto-fallback instances
│   ├── newsapi_fetcher.py          # NewsAPI.org (optional)
│   └── wechat_scraper.py           # WeChat articles via Sogou search (multi-strategy timestamp extraction)
├── processing/
│   ├── deduplicator.py             # URL + cross-lingual embedding dedup
│   ├── relevance_filter.py         # Keyword-based pre-filter
│   └── summarizer.py               # Two-tier LLM ranking (L1 screen + L2 deep analysis)
├── output/
│   ├── formatter.py                # Markdown + terminal formatters
│   └── file_writer.py              # Save digest to file
├── models/
│   └── article.py                  # Pydantic data models
├── digests/                        # Daily digest output files
└── logs/                           # Cron job logs
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

## Recent Improvements

**Two-tier LLM ranking (L1 + L2):**
- L1 uses a fast/cheap model (e.g. `gpt-4o-mini`) to screen 80 articles down to 25
- L2 uses a stronger model (e.g. `gpt-4o` or `gpt-5-mini`) for deep analysis and final ranking
- Set `L2_ENABLED=false` to use a single model for both stages

**Guaranteed top 15 output:**
- L2 prompt explicitly requires all articles to be returned
- `max_tokens` increased to 8192 to prevent JSON truncation
- Any articles the LLM skips are backfilled with L1 scores as fallback

**Cross-lingual embedding deduplication:**
- Uses OpenAI embeddings (`text-embedding-3-small`) to detect duplicate stories across English and Chinese
- Catches same-story-different-outlet duplicates that URL dedup misses

**RSSHub fallback resilience:**
- When the primary RSSHub instance (`rsshub.app`) returns 403 or is unreachable, automatically tries 4 fallback public instances
- Failed routes log a single clean warning instead of per-attempt noise
- Removed permanently broken feeds (FreeBuf, The Sequence)

**WeChat timestamp extraction:**
- 4-strategy extraction: `timeConvert()` script → `data-*` attributes → raw Unix timestamps → current time fallback
- WeChat articles now always display a publish date in the digest

**GitHub Actions CI/CD:**
- Automated daily digest at 07:00 UTC with auto-commit to `digests/`
- Manual trigger via workflow_dispatch
- All secrets configurable via GitHub Settings

## License

Internal use.
