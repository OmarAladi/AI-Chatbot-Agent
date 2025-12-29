"""
Prompt loader.

We keep prompts in text files under cob_demo_agent/prompts for easier iteration.
"""
from __future__ import annotations

from cob_demo_agent.utils.paths import PROMPTS_DIR

def _read(name: str) -> str:
    p = PROMPTS_DIR / name
    return p.read_text(encoding="utf-8") if p.exists() else ""

ROUTER_PROMPT = _read("router_prompt.txt")
RAG_PROMPT = _read("rag_prompt.txt")
BOOKING_PROMPT = _read("booking_prompt.txt")
HANDOFF_PROMPT = _read("handoff_prompt.txt")
