"""
FastAPI routes for chatting with the LangGraph agent.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from cob_demo_agent.schemas.chat import ChatRequest, ChatResponse
from cob_demo_agent.sre.graph_service import get_graph_service
from cob_demo_agent.utils.errors import classify_exception

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, svc=Depends(get_graph_service)) -> ChatResponse:
    """
    Run one turn of the agent for a given thread_id.

    Notes:
        - Each request is one user message.
        - Conversation state is retained in-memory via the graph checkpointer.
    """
    try:
        out = svc.invoke(req.message, thread_id=req.thread_id)
        return ChatResponse(**out)
    except Exception as exc:
        info = classify_exception(exc)
        raise HTTPException(status_code=info.status_code, detail={"error": info.kind, "message": info.message})
