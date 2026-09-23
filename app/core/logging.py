"""Structured logging setup.

Every log line goes through the standard logging module configured here.
Call sites are responsible for never passing raw secrets into a log
message; `redact_credentials_in_url` is provided for the one place that
legitimately needs to log a repository URL.
"""

from __future__ import annotations

import logging
import sys
from urllib.parse import urlsplit, urlunsplit

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger once per process."""

    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers = [handler]
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def redact_credentials_in_url(url: str) -> str:
    """Strip userinfo (token/password) from a URL before it is logged.

    ``https://x-access-token:ghp_xxx@github.com/org/repo.git`` becomes
    ``https://github.com/org/repo.git``. Never log the unredacted form.
    """

    try:
        parts = urlsplit(url)
    except ValueError:
        return "<unparseable-url>"

    if not parts.username and not parts.password:
        return url

    netloc = parts.hostname or ""
    if parts.port:
        netloc = f"{netloc}:{parts.port}"

    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
