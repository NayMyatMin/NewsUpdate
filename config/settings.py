import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# LLM Provider: "anthropic" or "openai"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# OpenAI (also works with any OpenAI-compatible API: Azure, local vLLM, Ollama, etc.)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")  # Leave empty for official OpenAI

# Two-tier LLM: L2 uses a stronger model for final ranking of L1-screened articles
L2_ENABLED = os.getenv("L2_ENABLED", "true").lower() in ("true", "1", "yes")
L2_OPENAI_MODEL = os.getenv("L2_OPENAI_MODEL", "gpt-4o")
L2_ANTHROPIC_MODEL = os.getenv("L2_ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Embedding model for cross-lingual deduplication
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# News APIs (optional)
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY", "")

# RSSHub base URL
RSSHUB_BASE_URL = os.getenv("RSSHUB_BASE_URL", "https://rsshub.app")

# Pipeline settings
MAX_ARTICLES_TO_L1 = 80           # Max articles sent to L1 (cheap) LLM screening
L1_PASS_COUNT = 25                # Articles that survive L1 for L2 deep scoring
TOP_N_OUTPUT = 15                 # Number of items in final digest
FETCH_TIMEOUT_SECONDS = 30        # Per-source fetch timeout
DEDUP_SIMILARITY_THRESHOLD = 0.82 # Cosine similarity for embedding dedup (pre-ranking)
EVENT_DEDUP_THRESHOLD = float(os.getenv("EVENT_DEDUP_THRESHOLD", "0.55"))  # Post-ranking same-event dedup (lower = stricter)
RELEVANCE_KEYWORD_MIN_SCORE = 1.5 # Minimum keyword score to pass pre-filter
MAX_ARTICLE_AGE_HOURS = int(os.getenv("MAX_ARTICLE_AGE_HOURS", "48"))  # Discard articles older than this

# Output paths
DIGESTS_DIR = PROJECT_ROOT / "digests"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure output directories exist
DIGESTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
