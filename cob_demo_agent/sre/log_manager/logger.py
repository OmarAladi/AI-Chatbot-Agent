"""
Logging configuration (file + console) with request correlation.

- Writes to logs/app.log (Rotating).
- Produces consistent, readable logs that help trace graph execution and tool calls.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from cob_demo_agent.utils.paths import LOGS_DIR

_LOGGER_INITIALIZED = False

def setup_logging(log_file: Optional[str] = None, level: str = "INFO") -> None:
    """
    Configure application logging. Safe to call multiple times.

    Args:
        log_file: Optional custom log path. Defaults to logs/app.log.
        level: Logging level name (e.g., "DEBUG", "INFO").
    """
    global _LOGGER_INITIALIZED
    if _LOGGER_INITIALIZED:
        return

    Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_file) if log_file else (Path(LOGS_DIR) / "app.log")

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler(
        filename=str(log_path),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)

    _LOGGER_INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)
