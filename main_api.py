"""
FastAPI entrypoint.

Run:
  uvicorn main_api:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cob_demo_agent.sre.log_manager.logger import setup_logging
from cob_demo_agent.routes.chat import router as chat_router

# Initialize logging as early as possible
setup_logging()

app = FastAPI(
    title="COB Demo Agent API",
    version="1.0.0",
)

# CORS (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    """Simple health check."""
    return {"status": "ok"}

app.include_router(chat_router, prefix="/api")
