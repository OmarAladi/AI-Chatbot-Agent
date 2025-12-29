"""
Environment helpers.

All secrets (API keys) should be provided via environment variables or a .env file.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

# Load .env from the project root by default (safe no-op if missing).
load_dotenv()

def get_env(name: str, default: str | None = None, required: bool = False) -> str | None:
    """
    Read an environment variable.

    Args:
        name: Environment variable name.
        default: Default value if not set.
        required: If True, raises ValueError when missing.

    Returns:
        The environment variable value (or default).
    """
    val = os.getenv(name, default)
    if required and (val is None or str(val).strip() == ""):
        raise ValueError(f"Missing required environment variable: {name}")
    return val
