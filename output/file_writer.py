import logging
from pathlib import Path

from config.settings import DIGESTS_DIR
from models.article import Digest
from output.formatter import format_digest_markdown

logger = logging.getLogger(__name__)


def save_digest(digest: Digest) -> Path:
    """Save the digest as a Markdown file and return the file path."""
    filename = f"{digest.date}.md"
    filepath = DIGESTS_DIR / filename

    content = format_digest_markdown(digest)
    filepath.write_text(content, encoding="utf-8")

    logger.info(f"Digest saved to {filepath}")
    return filepath
