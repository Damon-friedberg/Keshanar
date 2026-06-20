"""Capture: talk out loud + show your screen -> compiled tasks / to-dos / knowledge.

- capture(narration, png): one screenshot + what you said -> structured items.
- compile_session(steps): a whole walkthrough compiled into one deduplicated set.

Reliability lessons applied (from studying Claude structured-output + capture tools):
- Schema is GUARANTEED via forced tool-use (`record_capture`), not "respond with
  JSON" + brace-scraping — so a stray word can't silently drop the whole capture.
- Precision prompt: extract ONLY what's grounded in the screen/narration; never
  infer due dates or priorities; empty lists instead of padding.
- Light PII redaction on narration text before it leaves the machine.
Then store.save() writes Obsidian-native markdown to the local vault/ (with dedup).
"""
import re

from . import config, store, vision

_client = None


def _client_get():
    global _client
    if _client is None:
        from anthropic import Anthropic

        _client = Anthropic()
    return _client


_SYSTEM = (
    "You are Jarvis's capture engine. The user is narrating what is on their "
    "screen — customers, work, things to do. Convert ONLY what is explicitly "
    "shown on screen or explicitly said into structured items.\n"
    "Precision over recall — a wrong item is worse than a missing one:\n"
    "- Extract an item ONLY if directly supported by the screenshot or narration. "
    "Do not infer, guess, or generalize.\n"
    "- If the user did not state a due date or priority, set them to null. Never "
    "invent dates.\n"
    "- If a category has nothing explicit, return an empty list.\n"
    "- Prefer the user's own wording; keep titles short and actionable.\n"
    "- Link an item to a customer/project ONLY if that link is stated or clearly "
    "on screen."
)

# JSON Schema enforced by the model via tool-use (grammar-constrained).
_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "tasks", "todos", "knowledge", "customers"],
    "properties": {
        "summary": {"type": "string"},
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "due", "project", "customer", "priority"],
                "properties": {
                    "title": {"type": "string"},
                    "due": {"type": ["string", "null"]},
                    "project": {"type": ["string", "null"]},
                    "customer": {"type": ["string", "null"]},
                    "priority": {"type": ["string", "null"], "enum": ["low", "med", "high", None]},
                },
            },
        },
        "todos": {"type": "array", "items": {"type": "string"}},
        "knowledge": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["topic", "note", "customer"],
                "properties": {
                    "topic": {"type": "string"},
                    "note": {"type": "string"},
                    "customer": {"type": ["string", "null"]},
                },
            },
        },
        "customers": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "detail"],
                "properties": {"name": {"type": "string"}, "detail": {"type": "string"}},
            },
        },
    },
}

_TOOL = {
    "name": "record_capture",
    "description": "Record the tasks/todos/knowledge/customers extracted from screen + narration.",
    "input_schema": _SCHEMA,
}

# Cheap PII guard for narration text (the image itself is not redacted — see README).
_PII = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "<email>"),
    (re.compile(r"\b(?:\d[ -]?){13,16}\b"), "<card>"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "<ssn>"),
    (re.compile(r"\b(sk|pk|ghp|xox[bp])[-_][A-Za-z0-9]{8,}\b"), "<secret>"),
]


def redact(text: str) -> str:
    for rx, repl in _PII:
        text = rx.sub(repl, text or "")
    return text


def _img(png: bytes) -> dict:
    return {"type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": vision.to_b64(png)}}


def _extract(blocks: list) -> dict:
    msg = _client_get().messages.create(
        model=config.MODEL_HEAVY,
        max_tokens=2000,
        system=_SYSTEM,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "record_capture"},
        messages=[{"role": "user", "content": blocks}],
    )
    if getattr(msg, "stop_reason", None) == "max_tokens":
        print("[capture] warning: response truncated (raise max_tokens or split the session)")
    data = None
    for block in msg.content:
        if getattr(block, "type", "") == "tool_use" and block.name == "record_capture":
            data = block.input
            break
    if data is None:
        print("[capture] no structured output returned")
        data = {"summary": "(capture failed)", "tasks": [], "todos": [], "knowledge": [], "customers": []}
    store.save(data)
    return data


def capture(narration: str, png: bytes) -> dict:
    return _extract([_img(png),
                     {"type": "text", "text": f"Narration: {redact(narration) or '(none)'}"}])


def compile_session(steps: list) -> dict:
    """steps = list of (narration, png). Cap images to stay cheap; keep all text."""
    imgs = steps
    if len(steps) > 4:
        k = max(1, len(steps) // 4)
        imgs = steps[::k][:4]
    blocks: list = []
    for i, (_, png) in enumerate(imgs, 1):
        blocks += [{"type": "text", "text": f"[screen {i}]"}, _img(png)]
    narration = "\n".join(f"- {redact(n)}" for n, _ in steps if n)
    blocks.append({"type": "text", "text": f"Full narration:\n{narration}"})
    return _extract(blocks)


def spoken_summary(data: dict) -> str:
    s = data.get("summary", "Captured.")
    return (f"{s}. Logged {len(data.get('tasks', []))} tasks, "
            f"{len(data.get('todos', []))} to-dos, {len(data.get('knowledge', []))} notes, "
            f"{len(data.get('customers', []))} customer details.")
