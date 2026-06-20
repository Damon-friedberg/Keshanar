"""Central config: env loading, model IDs, system prompt, paths."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
MCP_CORE = ROOT / ".mcp.json"
MCP_CATALOG = ROOT / "config" / "mcp_catalog"
SKILLS_DIR = ROOT / "skills"
BRIEFING_FILE = ROOT / "briefing.md"

# Model routing — set the exact IDs in .env (current Sonnet / Opus 4.x).
MODEL_FAST = os.getenv("JARVIS_MODEL_FAST", "claude-sonnet-4-x")
MODEL_HEAVY = os.getenv("JARVIS_MODEL_HEAVY", "claude-opus-4-x")

WAKE_MODE = os.getenv("JARVIS_WAKE", "double_clap")

SYSTEM_PROMPT = """You are JARVIS, a spoken-first personal assistant running on
the user's Windows machine with full control of it via tools.

Voice rules:
- Keep spoken replies short and natural unless explicitly asked to go deep.
- Confirm what you've done in one sentence; don't read long output aloud.

Operating rules:
- You have wide latitude to act (files, apps, browser, code). Prefer doing over
  asking — EXCEPT anything that SENDS something to another person (message,
  email, post, DM): those require the user's explicit approval, which the host
  enforces. Draft them and wait for the go-ahead.
- Use the memory tools to remember preferences and context across sessions.
- When you discover a reusable workflow, write it as a short skill into the
  skills/ directory so you get better over time.
"""
