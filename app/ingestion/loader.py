"""Safe file loading.

Repository content is untrusted text: it is only ever read and decoded
here, never executed, imported, or passed to a shell.
"""

from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)


def load_file_text(path: Path) -> str | None:
    """Read a file as text, or return None if it can't be decoded as text."""

    try:
        return path.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            logger.warning("could not read file: %s", path.name)
            return None
    except OSError:
        logger.warning("could not read file: %s", path.name)
        return None
