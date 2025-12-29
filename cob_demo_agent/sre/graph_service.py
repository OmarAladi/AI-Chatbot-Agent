"""
Graph service: builds the LangGraph agent and exposes a stable invoke() interface.

Important:
- We preserve the notebook logic for node functions and graph wiring.
- We add logging and defensive error handling around invocation (without changing node behavior).
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from cob_demo_agent.sre.log_manager.logger import get_logger
from cob_demo_agent.utils.errors import classify_exception
from cob_demo_agent.utils.env import get_env

logger = get_logger("cob_demo_agent.graph_service")

_GRAPH_SERVICE_SINGLETON = None

def get_graph_service():
    """FastAPI dependency that returns a singleton GraphService."""
    global _GRAPH_SERVICE_SINGLETON
    if _GRAPH_SERVICE_SINGLETON is None:
        _GRAPH_SERVICE_SINGLETON = GraphService()
    return _GRAPH_SERVICE_SINGLETON


class GraphService:
    """
    Wraps the compiled LangGraph app.

    This provides:
    - request-level logging
    - retries for transient upstream failures (small, bounded)
    - normalized output for API responses
    """

    def __init__(self) -> None:
        from cob_demo_agent.sre.langgraph_app import build_app  # local import to avoid heavy import at module load
        self._app = build_app()

        # Bounded retries for transient errors (quota/timeouts)
        self._max_retries = int(get_env("COB_MAX_RETRIES", "1") or "1")

    def invoke(self, message: str, thread_id: str = "default") -> Dict[str, Any]:
        """
        Invoke the graph for a single user message.

        Args:
            message: The user message text.
            thread_id: Conversation id (checkpointer key).

        Returns:
            Dict containing reply + metadata used by ChatResponse.
        """
        cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}

        start = time.time()
        logger.info(f"[invoke] thread_id={thread_id} message={message[:200]!r}")

        last_exc: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                state = self._app.invoke(
                    {"messages": [{"role": "user", "content": message}]},
                    cfg,
                )
                break
            except Exception as exc:
                last_exc = exc
                info = classify_exception(exc)
                logger.exception(f"[invoke_error] attempt={attempt} kind={info.kind} raw={info.raw}")
                if not info.retryable or attempt >= self._max_retries:
                    raise
                # small backoff
                time.sleep(0.5 * (attempt + 1))
        else:
            raise last_exc  # pragma: no cover

        elapsed = (time.time() - start) * 1000
        logger.info(f"[invoke_done] thread_id={thread_id} elapsed_ms={elapsed:.1f}")

        # Normalize response from state
        messages = state.get("messages", [])
        reply = ""
        if messages:
            # last message is expected to be AIMessage, but keep it generic
            last = messages[-1]
            reply = getattr(last, "content", "") or ""

        route = state.get("route", "general")
        rag_meta_ids = state.get("rag_meta_ids", []) or []
        handoff_required = bool(state.get("handoff_required", False))
        handoff_reason = state.get("handoff_reason", "") or ""

        return {
            "reply": reply,
            "route": route,
            "rag_meta_ids": rag_meta_ids,
            "handoff_required": handoff_required,
            "handoff_reason": handoff_reason,
            "debug": None,
        }
