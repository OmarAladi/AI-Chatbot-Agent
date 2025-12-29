"""
RAG vector store setup (Chroma + Gemini embeddings).

Direct port from the notebook, with path/env safe defaults.

Environment:
- GOOGLE_API_KEY: required for embeddings
- COB_PERSIST_DIR: directory for Chroma persistence
- COB_KB_JSON_PATH: path to KB json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from cob_demo_agent.utils.env import get_env
from cob_demo_agent.utils.paths import DATA_DIR
from cob_demo_agent.sre.log_manager.logger import get_logger

logger = get_logger("cob_demo_agent.rag_vectorstore")

# Keep original variable names (but make them project-friendly)
PERSIST_DIR = get_env("COB_PERSIST_DIR", str(DATA_DIR / "chroma_langchain_db"))
COLLECTION_NAME = get_env("COB_COLLECTION_NAME", "cob_kb")
KB_JSON_PATH = get_env("COB_KB_JSON_PATH", str(DATA_DIR / "cob_kb.json"))

def _load_kb_items(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        logger.warning(f"KB JSON not found at {p}. RAG route will have empty context.")
        return []
    return json.loads(p.read_text(encoding="utf-8"))

def ensure_kb_indexed(vector_store: Chroma) -> None:
    """
    Ensure the KB is indexed into the vector store.

    This mimics the notebook behavior: load JSON docs and add to Chroma.
    """
    try:
        # If collection already has items, skip (cheap check)
        existing = vector_store._collection.count()  # type: ignore[attr-defined]
        if existing and existing > 0:
            return
    except Exception:
        # If count isn't available, proceed to add documents
        pass

    items = _load_kb_items(KB_JSON_PATH)
    docs: List[Document] = []
    for it in items:
        text = (it.get("text") or "").strip()
        if not text:
            continue
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "id": it.get("id", ""),
                    "title": it.get("title", ""),
                    "category": it.get("category", ""),
                    "source_file": it.get("source_file", ""),
                    "paragraph_index": it.get("paragraph_index", 0),
                    "lang": it.get("lang", "en"),
                },
            )
        )

    if not docs:
        logger.warning("No KB docs found to index.")
        return

    logger.info(f"Indexing KB docs into Chroma: n={len(docs)}")
    vector_store.add_documents(docs)

def build_retriever():
    """Create embeddings, Chroma vector store and return a retriever."""
    api_key = get_env("GOOGLE_API_KEY", required=True)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        api_key=api_key,
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR,
    )

    ensure_kb_indexed(vector_store)

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},
    )
    return retriever
