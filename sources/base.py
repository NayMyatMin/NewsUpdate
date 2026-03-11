from abc import ABC, abstractmethod
from models.article import Article


class BaseFetcher(ABC):
    """Abstract base class for all news source fetchers."""

    @abstractmethod
    async def fetch(self) -> list[Article]:
        """Fetch articles from this source. Returns list of Article objects."""
        ...
