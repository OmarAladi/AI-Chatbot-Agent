"""
Error classification utilities.

We convert common model / provider / network errors into stable categories so the API
can respond consistently.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

@dataclass
class ErrorInfo:
    """Normalized error info."""
    kind: str
    message: str
    status_code: int = 500
    retryable: bool = False
    raw: Optional[str] = None


def classify_exception(exc: Exception) -> ErrorInfo:
    """
    Try to classify an exception into a stable error category.

    This intentionally uses broad checks to support multiple LLM providers / SDKs.

    Returns:
        ErrorInfo
    """
    msg = str(exc)
    low = msg.lower()

    # Quota / rate limit / resource exhausted
    if "resource exhausted" in low or "quota" in low or "rate limit" in low or "429" in low:
        return ErrorInfo(
            kind="MODEL_QUOTA_EXCEEDED",
            message="Model quota/rate limit exceeded. Please retry later.",
            status_code=429,
            retryable=True,
            raw=msg,
        )

    # Timeouts / transient network
    if "timeout" in low or "timed out" in low or "temporarily unavailable" in low or "503" in low:
        return ErrorInfo(
            kind="TRANSIENT_UPSTREAM_ERROR",
            message="Upstream service temporarily unavailable. Please retry.",
            status_code=503,
            retryable=True,
            raw=msg,
        )

    # Bad request / validation at provider side
    if "invalid" in low or "bad request" in low or "400" in low:
        return ErrorInfo(
            kind="UPSTREAM_BAD_REQUEST",
            message="Upstream rejected the request (invalid input/config).",
            status_code=400,
            retryable=False,
            raw=msg,
        )

    return ErrorInfo(
        kind="INTERNAL_ERROR",
        message="Unexpected server error.",
        status_code=500,
        retryable=False,
        raw=msg,
    )
