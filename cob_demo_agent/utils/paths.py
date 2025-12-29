"""
Centralized filesystem paths for the project.

We keep the original variable names (e.g., DB_PATH, PERSIST_DIR) in the agent modules,
but these helpers provide sensible defaults for a real project layout.
"""
from __future__ import annotations

from pathlib import Path
from .env import get_env

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../cob_demo_agent
PACKAGE_ROOT = Path(__file__).resolve().parents[1]  # .../cob_demo_agent/cob_demo_agent

LOGS_DIR = Path(get_env("COB_LOGS_DIR", str(PROJECT_ROOT / "logs"))).resolve()
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path(get_env("COB_DATA_DIR", str(PROJECT_ROOT / "data"))).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROMPTS_DIR = PACKAGE_ROOT / "prompts"
