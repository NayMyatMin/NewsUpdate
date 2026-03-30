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
    topic_matches: list[str] = Field(default_factory=list)


class Digest(BaseModel):
    date: str
    generated_at: datetime
    total_fetched: int
    total_after_freshness: int = 0
    total_after_dedup: int
    total_after_filter: int
    top_articles: list[RankedArticle]
