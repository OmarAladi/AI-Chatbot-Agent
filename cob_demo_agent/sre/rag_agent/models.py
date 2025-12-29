"""
Pydantic / structured output models for router, rag and handoff decisions.

These are copied from the notebook structure (same field names and semantics).
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Literal

class RouterDecision(BaseModel):
    """
    Router decides one of 4 routes.
    - general: router replies directly
    - kb: go to RAG node
    - booking: go to booking flow
    - handoff: go to handoff node
    """
    route: Literal["general", "kb", "booking", "handoff"] = Field(...)
    reply: str = Field(default="")  # used only if route == "general"
    confidence: float = Field(default=0.7)

class MetaChunk(BaseModel):
    id: str = Field(default="")
    title: str = Field(default="")
    category: str = Field(default="")
    source_file: str = Field(default="")
    paragraph_index: int = Field(default=0)

class StructuredResponseRAG(BaseModel):
    answer: str = Field(...)
    meta: List[MetaChunk] = Field(default_factory=list)

class HandoffDecision(BaseModel):
    handoff_required: bool = Field(default=False)
    reason: str = Field(default="")
    reply: str = Field(default="")
