"""How Jarvis learns *you* and adapts — the personalization layer.

Two tiers (how good assistants actually do it):
- PROFILE (here): a compact, always-injected summary — identity, preferences,
  communication style, people, projects, do/don't. Cheap; goes in EVERY turn so
  Jarvis adapts to you immediately.
- DEEP MEMORY (Graphiti / basic-memory MCP): the evolving, queryable, time-aware
  knowledge graph the agent reads/writes via tools for the long tail.

Updated explicitly ("remember…", "I prefer…", corrections) and consolidated
nightly by briefing.py. Lives in vault/ (gitignored — it's yours, stays local).
"""
import json
from datetime import date

from . import config

PROFILE_JSON = config.ROOT / "vault" / ".profile.json"
PROFILE_MD = config.ROOT / "vault" / "profile.md"


def _blank() -> dict:
    return {"identity": {}, "preferences": [], "style": [], "people": {},
            "projects": {}, "dos": [], "donts": []}


def load() -> dict:
    if PROFILE_JSON.exists():
        try:
            return {**_blank(), **json.loads(PROFILE_JSON.read_text())}
        except Exception:  # noqa: BLE001
            pass
    return _blank()


def save(p: dict) -> None:
    PROFILE_JSON.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_JSON.write_text(json.dumps(p, indent=2))
    PROFILE_MD.write_text(_md(p))


def prompt() -> str:
    """Compact profile block injected into the system prompt every turn."""
    p = load()
    if not (any(p["identity"]) or any(p[k] for k in
            ("preferences", "style", "people", "projects", "dos", "donts"))):
        return ""
    out = ["\n\nWHAT YOU KNOW ABOUT THE USER (adapt to this; honor it unless they say otherwise):"]
    if p["identity"]:
        out.append("- Identity: " + ", ".join(f"{k}: {v}" for k, v in p["identity"].items()))
    if p["preferences"]:
        out.append("- Prefers: " + "; ".join(p["preferences"]))
    if p["style"]:
        out.append("- Communication style: " + "; ".join(p["style"]))
    if p["dos"]:
        out.append("- Do: " + "; ".join(p["dos"]))
    if p["donts"]:
        out.append("- Don't: " + "; ".join(p["donts"]))
    if p["people"]:
        out.append("- People: " + "; ".join(f"{k} ({v})" for k, v in p["people"].items()))
    if p["projects"]:
        out.append("- Projects: " + "; ".join(f"{k} ({v})" for k, v in p["projects"].items()))
    return "\n".join(out)


def _merge(p: dict, delta: dict) -> dict:
    for k, v in (delta.get("identity") or {}).items():
        if v:
            p["identity"][k] = v
    for k in ("preferences", "style", "dos", "donts"):
        for item in delta.get(k) or []:
            if item and item not in p[k]:
                p[k].append(item)
    for k in ("people", "projects"):
        for name, note in (delta.get(k) or {}).items():
            if name:
                p[k][name] = note
    return p


_client = None


def _client_get():
    global _client
    if _client is None:
        from anthropic import Anthropic
        _client = Anthropic()
    return _client


_LEARN_TOOL = {
    "name": "update_profile",
    "description": "Record durable facts/preferences about the user from what they just said.",
    "input_schema": {
        "type": "object", "additionalProperties": False,
        "required": ["identity", "preferences", "style", "people", "projects", "dos", "donts"],
        "properties": {
            "identity": {"type": "object", "additionalProperties": {"type": "string"}},
            "preferences": {"type": "array", "items": {"type": "string"}},
            "style": {"type": "array", "items": {"type": "string"}},
            "people": {"type": "object", "additionalProperties": {"type": "string"}},
            "projects": {"type": "object", "additionalProperties": {"type": "string"}},
            "dos": {"type": "array", "items": {"type": "string"}},
            "donts": {"type": "array", "items": {"type": "string"}},
        },
    },
}


def learn(text: str) -> dict:
    """Extract durable user facts/preferences from `text` and merge into the profile."""
    msg = _client_get().messages.create(
        model=config.MODEL_FAST,
        max_tokens=700,
        system=("Extract ONLY durable facts/preferences about the user worth "
                "remembering long-term (identity, how they like things done, "
                "people, projects, do/don't). Ignore one-off requests. Use the "
                "user's own wording. Empty objects/arrays if nothing durable."),
        tools=[_LEARN_TOOL],
        tool_choice={"type": "tool", "name": "update_profile"},
        messages=[{"role": "user", "content": text}],
    )
    delta: dict = {}
    for b in msg.content:
        if getattr(b, "type", "") == "tool_use":
            delta = b.input
            break
    save(_merge(load(), delta))
    return delta


def _md(p: dict) -> str:
    lines = [f"---\ntype: profile\nupdated: {date.today().isoformat()}\n---\n# About me\n"]
    if p["identity"]:
        lines.append("## Identity")
        lines += [f"- **{k}**: {v}" for k, v in p["identity"].items()]
    for key, label in [("preferences", "Preferences"), ("style", "Style"),
                       ("dos", "Do"), ("donts", "Don't")]:
        if p[key]:
            lines.append(f"\n## {label}")
            lines += [f"- {x}" for x in p[key]]
    if p["people"]:
        lines.append("\n## People")
        lines += [f"- **{k}** — {v}" for k, v in p["people"].items()]
    if p["projects"]:
        lines.append("\n## Projects")
        lines += [f"- **{k}** — {v}" for k, v in p["projects"].items()]
    return "\n".join(lines) + "\n"
