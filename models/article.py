from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Article(BaseModel):
    title: str
    url: str
    source: str  # e.g., "google_news", "36kr", "arxiv"
    language: str = "en"  # "en" or "zh"
    published: Optional[datetime] = None
    snippet: Optional[str] = None  # First 500 chars of content/description
    topic_matches: list[str] = Field(default_factory=list)


class RankedArticle(BaseModel):
    title: str
    url: str
    source: str
    language: str = "en"
    published: Optional[datetime] = None
    rank: int = 0
    relevance_score: float = 0.0
    summary: str = ""
    why_important: str = ""
    section: str = ""  # One of DIGEST_SECTIONS keys
    topic_matches: list[str] = Field(default_factory=list)


# Ordered section definitions for the digest
DIGEST_SECTIONS = {
    "threats_incidents": {
        "title": "Threats & Incidents",
        "description": "Active attacks, breaches, jailbreaks, CVEs, safety failures, vulnerability disclosures",
        "min_articles": 2,
    },
    "ai_security_industry": {
        "title": "AI Security from Major Players",
        "description": "AI safety/security announcements, tools, features, and guardrail releases from major companies",
        "min_articles": 2,
    },
    "ai_agents_os": {
        "title": "AI Agents & OS Integration",
        "description": "Agent features from Apple/Android/Windows/HarmonyOS, agent frameworks, platform-level agent controls",
        "min_articles": 0,
        "empty_message": "No significant developments today.",
    },
    "research_regulation": {
        "title": "Research & Regulation",
        "description": "Papers, benchmarks, safety standards, governance, policy changes",
        "min_articles": 2,
    },
}


class Digest(BaseModel):
    date: str
    generated_at: datetime
    total_fetched: int
    total_after_freshness: int = 0
    total_after_dedup: int
    total_after_filter: int
    top_articles: list[RankedArticle]
