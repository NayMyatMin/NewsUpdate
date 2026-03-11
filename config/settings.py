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

# News APIs (optional)
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY", "")

# RSSHub base URL
RSSHUB_BASE_URL = os.getenv("RSSHUB_BASE_URL", "https://rsshub.app")

# Pipeline settings
MAX_ARTICLES_TO_CLAUDE = 80  # Cost control: max articles sent to LLM
TOP_N_OUTPUT = 15  # Number of items in final digest (broader coverage)
FETCH_TIMEOUT_SECONDS = 30  # Per-source fetch timeout
DEDUP_SIMILARITY_THRESHOLD = 0.6  # Jaccard similarity for title dedup
RELEVANCE_KEYWORD_MIN_SCORE = 1.5  # Minimum keyword score to pass pre-filter

# Output paths
DIGESTS_DIR = PROJECT_ROOT / "digests"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure output directories exist
DIGESTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
