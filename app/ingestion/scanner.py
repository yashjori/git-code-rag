"""Repository file discovery.

Walks a checked-out repository directory and yields candidate file paths.
Security-relevant by design: this is the one place that decides which
directories get walked into at all, so it is where symlink escape and
ignored-directory pruning are enforced.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

from app.core.config import IGNORED_DIRECTORY_NAMES


def discover_files(root: Path) -> Iterator[Path]:
    """Yield every regular file under root, skipping ignored directories.

    ``followlinks=False`` (the os.walk default) means symlinked directories
    are never descended into. Symlinked files are skipped explicitly too, so
    a crafted symlink inside a cloned repository cannot be used to read
    content from outside the repository root.
    """

    root = root.resolve()

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRECTORY_NAMES]

        current_dir = Path(dirpath)
        for filename in filenames:
            file_path = current_dir / filename
            if file_path.is_symlink():
                continue
            resolved = file_path.resolve()
            if root not in resolved.parents and resolved != root:
                # Defense in depth: never yield a path that resolves outside
                # the repository root.
                continue
            yield file_path
