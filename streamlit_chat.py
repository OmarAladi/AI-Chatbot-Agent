"""
Streamlit Chat UI for COB Demo Agent (FastAPI backend).

Features:
- Wide + Dark UI (CSS)
- Session-scoped random thread_id (6 digits)
- Chat-like interface using st.chat_message/st.chat_input
- Sends: {message, thread_id}
- Displays: reply only
- If handoff_required == True:
  - Show last AI reply
  - Lock chat input (stop conversation)
  - Show a red flag under the AI message
"""

from __future__ import annotations

import os
import random
import requests
import streamlit as st
from typing import Dict, Any


# =========================
# Page config (Wide)
# =========================
st.set_page_config(
    page_title="COB Demo Agent",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================
# Dark UI CSS
# =========================
DARK_CSS = """
<style>
/* Make the whole app dark */
.stApp {
    background: #0b0f14;
    color: #e6edf3;
}

/* Wider container feel */
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Chat bubbles */
div[data-testid="stChatMessage"] {
    border-radius: 14px;
    padding: 10px 12px;
    margin-bottom: 10px;
}

/* User message bubble */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
    background: #0f1720;
    border: 1px solid #1f2a37;
}

/* Assistant message bubble */
div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
    background: #0c141d;
    border: 1px solid #1d2836;
}

/* Inputs dark */
textarea, input {
    background: #0f1720 !important;
    color: #e6edf3 !important;
    border: 1px solid #1f2a37 !important;
}

/* Red flag box */
.cob-flag {
    margin-top: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid rgba(255, 71, 87, 0.35);
    background: rgba(255, 71, 87, 0.12);
    color: #ff6b81;
    font-weight: 600;
}
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)


# =========================
# Backend URL
# =========================
# Example: http://127.0.0.1:8000/api/chat
BACKEND_CHAT_URL = os.getenv("COB_BACKEND_CHAT_URL", "http://127.0.0.1:8000/api/chat")


def ensure_session_state() -> None:
    """Initialize session state keys used by the UI."""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(random.randint(100000, 999999))  # 6 digits -> str

    if "messages" not in st.session_state:
        # Each item: {"role": "user"|"assistant", "content": "...", "flag": bool}
        st.session_state.messages = []

    if "handoff_locked" not in st.session_state:
        st.session_state.handoff_locked = False


def call_backend(message: str, thread_id: str) -> Dict[str, Any]:
    """
    Call FastAPI backend /api/chat.

    Payload:
      {"message": "...", "thread_id": "..."}
    Response expected:
      {"reply": "...", "route": "...", "handoff_required": bool, "handoff_reason": str, ...}
    """
    payload = {"message": message, "thread_id": thread_id}
    resp = requests.post(BACKEND_CHAT_URL, json=payload, timeout=120)

    # Raise nice error if backend returns non-2xx
    if not resp.ok:
        try:
            detail = resp.json()
        except Exception:
            detail = {"raw": resp.text}
        raise RuntimeError(f"Backend error ({resp.status_code}): {detail}")

    return resp.json()


# =========================
# UI Header
# =========================
ensure_session_state()

st.title("💬 COB Demo Agent")
st.caption(f"thread_id: `{st.session_state.thread_id}`  |  backend: `{BACKEND_CHAT_URL}`")

# Optional: small reset button
col1, col2, col3 = st.columns([1, 1, 6])
with col1:
    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.thread_id = str(random.randint(100000, 999999))
        st.session_state.messages = []
        st.session_state.handoff_locked = False
        st.rerun()


# =========================
# Render chat history
# =========================
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

        # Red flag under AI message when handoff triggers
        if m.get("flag", False) and m["role"] == "assistant":
            st.markdown(
                '<div class="cob-flag">🚩 Handoff required — chat is paused and needs human assistance.</div>',
                unsafe_allow_html=True,
            )


# =========================
# Chat input (locked on handoff)
# =========================
if st.session_state.handoff_locked:
    st.info("Chat is paused because the system requested a handoff. Start a New Chat to begin a fresh conversation.")
    st.stop()

user_text = st.chat_input("Type your message here...")

if user_text:
    # 1) Show user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # 2) Call backend and show assistant reply
    try:
        data = call_backend(user_text, st.session_state.thread_id)
        reply = (data.get("reply") or "").strip()
        handoff_required = bool(data.get("handoff_required", False))

        # We display reply only (as requested)
        st.session_state.messages.append(
            {"role": "assistant", "content": reply or "_(no reply)_", "flag": handoff_required}
        )

        with st.chat_message("assistant"):
            st.markdown(reply or "_(no reply)_")

            if handoff_required:
                st.markdown(
                    '<div class="cob-flag">🚩 Handoff required — chat is paused and needs human assistance.</div>',
                    unsafe_allow_html=True,
                )
                st.session_state.handoff_locked = True

    except Exception as e:
        # Show an error message bubble
        err_text = f"❌ An error occurred while connecting to the backend:\n\n{e}"
        st.session_state.messages.append({"role": "assistant", "content": err_text, "flag": False})
        with st.chat_message("assistant"):
            st.markdown(err_text)
