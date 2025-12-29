"""
Pydantic schemas for the public API.

These ensure input/output stability for clients.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class ChatRequest(BaseModel):
    """
    A single user message to the agent.

    thread_id is used by the LangGraph checkpointer to keep state per conversation.
    """
    message: str = Field(..., min_length=1, description="User message")
    thread_id: str = Field(default="default", description="Conversation thread id")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional client metadata")

class ChatResponse(BaseModel):
    """Agent response."""
    reply: str = Field(..., description="Assistant reply")
    route: str = Field(..., description="Chosen route (general|kb|booking|handoff)")
    rag_meta_ids: List[str] = Field(default_factory=list, description="Retrieved KB chunk ids (if any)")
    handoff_required: bool = Field(default=False)
    handoff_reason: str = Field(default="")
    debug: Optional[Dict[str, Any]] = Field(default=None, description="Optional debug payload (server-side)")
