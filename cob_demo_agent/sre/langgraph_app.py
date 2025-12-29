"""
LangGraph application builder.

This module is the "ported notebook" in a production layout:
- loads prompts
- builds LLMs
- builds retriever + tool nodes
- defines node functions and graph wiring

We aim to preserve the notebook's logic, while adding:
- safe config via env vars
- structured logging around node execution
- bounded tool loops (if present in notebook)
"""
from __future__ import annotations

from typing import Annotated, Literal, Dict, Any, Optional, List
from typing_extensions import TypedDict

from cob_demo_agent.sre.log_manager.logger import get_logger
from cob_demo_agent.utils.env import get_env

from langchain.chat_models import init_chat_model
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode

from cob_demo_agent.sre.booking_agent.tools import list_available_slots, check_slot_availability, book_slot
from cob_demo_agent.sre.rag_agent.vectorstore import build_retriever
from cob_demo_agent.sre.rag_agent.models import RouterDecision, StructuredResponseRAG, HandoffDecision
from cob_demo_agent.sre.rag_agent.prompts import ROUTER_PROMPT, RAG_PROMPT, BOOKING_PROMPT, HANDOFF_PROMPT

logger = get_logger("cob_demo_agent.langgraph_app")

# Tools list (kept same semantics)
BOOKING_TOOLS = [list_available_slots, check_slot_availability, book_slot]

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    route: Literal["general", "kb", "booking", "handoff"]
    rag_meta_ids: list[str]
    handoff_required: bool
    handoff_reason: str
    booking_tool_steps: int
    last_tool_signature: str
    repeat_tool_count: int

def _wrap_node(name: str, fn):
    """Log entry/exit for a node without changing its behavior."""
    def _inner(state: State):
        try:
            last = state["messages"][-1] if state.get("messages") else None
            last_type = type(last).__name__ if last is not None else "None"
            last_preview = (getattr(last, "content", "") or "")[:200] if last is not None else ""
            logger.info(f"[node_enter] {name} last_type={last_type} last={last_preview!r}")
            out = fn(state)
            # Log route/tool hints
            route = out.get("route", state.get("route"))
            logger.info(f"[node_exit] {name} route={route!r} keys={list(out.keys())}")
            return out
        except Exception:
            logger.exception(f"[node_error] {name}")
            raise
    return _inner

def build_app():
    """
    Build and compile the LangGraph app.

    Returns:
        Compiled graph app with an in-memory checkpointer.
    """
    api_key = get_env("GOOGLE_API_KEY", required=True)
    router_llm_api_key = get_env("ROUTER_API_KEY", required=True)
    rag_llm_tools_api_key = get_env("RAG_API_KEY", required=True)
    booking_llm_api_key = get_env("BOOKING_API_KEY", required=True)
    handoff_llm_api_key = get_env("HANDOFF_API_KEY", required=True)

    # LLMs (ported settings)
    router_llm = init_chat_model(
        model=get_env("COB_ROUTER_MODEL", "google_genai:gemini-flash-latest"),
        temperature=float(get_env("COB_ROUTER_TEMP", "1") or "1"),
        api_key=router_llm_api_key,
    ).with_structured_output(RouterDecision, method="function_calling")

    rag_llm_tools = init_chat_model(
        model=get_env("COB_RAG_MODEL", "google_genai:gemini-flash-latest"),
        temperature=float(get_env("COB_RAG_TEMP", "0") or "0"),
        api_key=rag_llm_tools_api_key,
    ).with_structured_output(StructuredResponseRAG, method="function_calling")

    booking_llm = init_chat_model(
        model=get_env("COB_BOOKING_MODEL", "google_genai:gemini-flash-latest"),
        temperature=float(get_env("COB_BOOKING_TEMP", "0.2") or "0.2"),
        api_key=booking_llm_api_key,
    ).bind_tools(BOOKING_TOOLS)

    handoff_llm = init_chat_model(
        model=get_env("COB_HANDOFF_MODEL", "google_genai:gemini-flash-latest"),
        temperature=float(get_env("COB_HANDOFF_TEMP", "1") or "1"),
        api_key=handoff_llm_api_key,
    ).with_structured_output(HandoffDecision, method="function_calling")

    retriever = build_retriever()

    # ----------------------------
    # Node functions (ported logic)
    # ----------------------------
    def router_node(state: State) -> State:
        last_user = state["messages"][-1]
        if not isinstance(last_user, HumanMessage):
            return state

        router_system = SystemMessage(content=ROUTER_PROMPT)
        decision: RouterDecision = router_llm.invoke([router_system] + state["messages"])

        # Confidence guard (not keyword rules): if unsure, ask one question in general route
        if decision.confidence < 0.55 and decision.route != "general":
            decision.route = "general"
            if not decision.reply.strip():
                decision.reply = (
                    "Could you clarify—are you trying to book a service or asking an informational question?"
                )

        updates: Dict[str, Any] = {"route": decision.route}

        # Router answers directly if general
        if decision.route == "general":
            reply = decision.reply
            updates["messages"] = [AIMessage(content=reply)]
            return updates

        return updates

    def route_after_router(state: State) -> str:
        if state["route"] == "kb":
            return "rag_node"
        if state["route"] == "booking":
            return "booking_llm_node"
        if state["route"] == "handoff":
            return "handoff_node"
        return END

    def rag_node(state: State) -> State:
        query = state["messages"][-1].content

        # 1. Retrieve first (no LLM)
        kb_context = retriever.invoke(query)

        # 2. Build prompt + messages
        ctx_text = "\n\n".join([d.page_content for d in kb_context]) if kb_context else ""
        system = SystemMessage(content=RAG_PROMPT)
        msgs = [system] + state["messages"] + [SystemMessage(content=f"KB_CONTEXT:\n{ctx_text}")]

        # 3. Single LLM call
        ai_structured_response = rag_llm_tools.invoke(msgs)

        # Extract chunk ids safely
        rag_meta_ids = [m.id for m in ai_structured_response.meta if m.id]

        # Convert StructuredResponseRAG to AIMessage
        ai_message = AIMessage(
            content=ai_structured_response.answer,
            additional_kwargs={"rag_meta_ids": rag_meta_ids},
        )

        return {
            "messages": [ai_message],
            "rag_meta_ids": rag_meta_ids,
        }

    def booking_llm_node(state: State) -> State:
        booking_system = SystemMessage(content=BOOKING_PROMPT)
        ai = booking_llm.invoke([booking_system] + state["messages"])

        sig = ""
        if isinstance(ai, AIMessage) and getattr(ai, "tool_calls", None):
            tc = ai.tool_calls[0]
            import json
            sig = tc["name"] + "|" + json.dumps(tc.get("args", {}), sort_keys=True)

        repeats = state.get("repeat_tool_count", 0)
        if sig and sig == state.get("last_tool_signature"):
            repeats += 1
        else:
            repeats = 0

        return {
            "messages": [ai],
            "last_tool_signature": sig,
            "repeat_tool_count": repeats,
        }

    MAX_TOOL_STEPS = int(get_env("COB_MAX_TOOL_STEPS", "4") or "4")

    def booking_should_continue(state: State) -> str:
        if state.get("booking_tool_steps", 0) >= MAX_TOOL_STEPS:
            return "end"
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
            # Stop if repeating the same tool call too many times
            if state.get("repeat_tool_count", 0) >= 2:
                return "end"
            return "continue"
        return "end"

    tool_node = ToolNode(tools=BOOKING_TOOLS)

    def tools_wrapper(state: State) -> State:
        out = tool_node.invoke(state)
        return {**out, "booking_tool_steps": state.get("booking_tool_steps", 0) + 1}

    def handoff_node(state: State) -> State:
        last_user = state["messages"][-1]
        if not isinstance(last_user, HumanMessage):
            return state

        router_system = SystemMessage(content=HANDOFF_PROMPT or ROUTER_PROMPT)
        decision: HandoffDecision = handoff_llm.invoke([router_system] + state["messages"])

        return {
            "handoff_required": bool(decision.handoff_required),
            "handoff_reason": decision.reason if decision.handoff_required else "",
            "messages": [AIMessage(content=decision.reply)],
        }

    # ----------------------------
    # Graph wiring (ported)
    # ----------------------------
    builder = StateGraph(State)

    builder.add_node("router_node", _wrap_node("router_node", router_node))
    builder.add_node("rag_node", _wrap_node("rag_node", rag_node))
    builder.add_node("booking_llm_node", _wrap_node("booking_llm_node", booking_llm_node))
    builder.add_node("tools", _wrap_node("tools", tools_wrapper))
    builder.add_node("handoff_node", _wrap_node("handoff_node", handoff_node))

    builder.set_entry_point("router_node")
    builder.add_conditional_edges("router_node", route_after_router)

    builder.add_conditional_edges(
        "booking_llm_node",
        booking_should_continue,
        {"continue": "tools", "end": END},
    )
    builder.add_edge("tools", "booking_llm_node")

    builder.add_edge("rag_node", END)
    builder.add_edge("handoff_node", END)

    checkpointer = InMemorySaver()
    app = builder.compile(checkpointer=checkpointer)
    return app
