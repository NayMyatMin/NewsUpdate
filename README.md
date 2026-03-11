# NewsUpdate Agent

Daily tech news digest powered by AI. Fetches 1,400+ articles from 55+ sources (international + Chinese), deduplicates, filters by relevance, and uses an LLM to rank and summarize the top 15 things you need to know.

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

All config lives in `.env`:

```bash
# LLM provider: "openai" (default) or "anthropic"
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o-mini          # cheapest, ~$0.03/day

# Or use any OpenAI-compatible API (Ollama, vLLM, Azure, etc.)
# OPENAI_BASE_URL=http://localhost:11434/v1

# Anthropic (if LLM_PROVIDER=anthropic)
# ANTHROPIC_API_KEY=sk-ant-xxxxx
# ANTHROPIC_MODEL=claude-haiku-4-5-20251001

# Optional: NewsAPI.org for extra international coverage
# NEWSAPI_KEY=xxxxx
```

## How It Works

```
Fetch (55+ sources, async)
  → 1,400+ raw articles
    → Deduplicate (URL + title similarity)
      → ~1,350 unique
        → Keyword relevance filter (17 topic clusters)
          → Top 80 candidates
            → LLM summarization & ranking
              → Top 15 digest
```

**Pipeline stages:**

| Stage | What it does | Cost |
|---|---|---|
| Fetch | Async RSS/scraping from all sources | Free |
| Dedup | URL + Jaccard title similarity | Free |
| Filter | Keyword matching across 17 topic clusters | Free |
| Summarize | LLM scores, summarizes, and ranks | ~$0.03-0.07/day |
| Output | Markdown file + terminal display | Free |

## Sources

### International (English)

**AI & ML:**
TechCrunch AI, Wired AI, MIT Tech Review, The Verge AI, ArXiv (cs.AI, cs.CR, cs.CL), Google AI Blog, OpenAI Blog, Hugging Face Blog, DeepMind Blog, Meta Engineering ML, Apple ML Blog, Microsoft AI Blog, Lil'Log, NLP Newsletter, The Sequence, Import AI

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
CLS Telegraph (财联社), FreeBuf, Seebug Paper, Xianzi (先知社区), InfoQ China

## Topic Clusters (17)

| Priority | Topics |
|---|---|
| High (3.0) | AI Safety & Alignment, AI Security & Attacks, Huawei Ecosystem |
| Medium-High (2.5) | LLMs, AI Agents, Cybersecurity & Incidents, AI Governance |
| Medium (2.0) | Frontier Models, Mobile/Telecom, Geopolitical AI, AI in Cybersecurity, Cloud & Infra, Privacy & Data |
| Standard (1.5) | Software & Dev Tools, Blockchain, Quantum Computing, Robotics & Hardware, Big Tech Business |

## Cost

| Provider | Model | Daily Cost | Monthly Cost |
|---|---|---|---|
| OpenAI | gpt-4o-mini | ~$0.03 | ~$1 |
| Anthropic | claude-haiku-4-5 | ~$0.07 | ~$2 |
| OpenAI | gpt-4o | ~$0.50 | ~$15 |
| Local (Ollama) | any | $0 | $0 |

## Run as Daily Cron Job

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
│   └── sources.py                  # 55+ source definitions
├── sources/
│   ├── rss_fetcher.py              # Async RSS/Atom feed parser
│   ├── google_news.py              # Google News RSS search (28 queries)
│   ├── rsshub_fetcher.py           # Chinese sources via RSSHub
│   ├── newsapi_fetcher.py          # NewsAPI.org (optional)
│   └── wechat_scraper.py           # WeChat articles via Sogou search
├── processing/
│   ├── deduplicator.py             # URL + title similarity dedup
│   ├── relevance_filter.py         # Keyword-based pre-filter
│   └── summarizer.py               # LLM summarization (OpenAI / Anthropic)
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

## License

Internal use.
