"""Capture: talk out loud + show your screen -> compiled tasks / to-dos / knowledge.

- capture(narration, png): one screenshot + what you said -> structured items.
- compile_session(steps): a whole walkthrough (several narration+screen steps)
  compiled into one deduplicated set.

Uses the Anthropic Messages API with vision directly (reliable structured JSON),
then store.save() writes everything to the local vault/.
"""
import json

from . import config, store, vision

_client = None


def _client_get():
    global _client
    if _client is None:
        from anthropic import Anthropic

        _client = Anthropic()
    return _client


_SYSTEM = (
    "You are Jarvis's capture engine. The user is talking through what is on their "
    "screen — customers, work, things they need to do. Combine the screenshot(s) "
    "and their narration into structured, deduplicated items."
)

_SCHEMA = """Respond with ONLY valid JSON (no prose, no code fence):
{
  "summary": "one short line of what this was about",
  "tasks": [{"title": "...", "due": "YYYY-MM-DD or null", "project": "... or null", "priority": "low|med|high"}],
  "todos": ["short actionable item"],
  "knowledge": [{"topic": "...", "note": "fact worth remembering"}],
  "customers": [{"name": "...", "detail": "what matters about them"}]
}
Include only items genuinely supported by the screen or narration."""


def _img(png: bytes) -> dict:
    return {"type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": vision.to_b64(png)}}


def _extract(blocks: list) -> dict:
    msg = _client_get().messages.create(
        model=config.MODEL_HEAVY,
        max_tokens=1600,
        system=_SYSTEM,
        messages=[{"role": "user", "content": blocks}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    data = _loads(text)
    store.save(data)
    return data


def capture(narration: str, png: bytes) -> dict:
    return _extract([_img(png),
                     {"type": "text", "text": f"Narration: {narration or '(none)'}\n\n{_SCHEMA}"}])


def compile_session(steps: list) -> dict:
    """steps = list of (narration, png). Cap images to stay cheap; keep all text."""
    imgs = steps
    if len(steps) > 4:
        k = max(1, len(steps) // 4)
        imgs = steps[::k][:4]
    blocks: list = []
    for i, (_, png) in enumerate(imgs, 1):
        blocks += [{"type": "text", "text": f"[screen {i}]"}, _img(png)]
    narration = "\n".join(f"- {n}" for n, _ in steps if n)
    blocks.append({"type": "text", "text": f"Full narration:\n{narration}\n\n{_SCHEMA}"})
    return _extract(blocks)


def spoken_summary(data: dict) -> str:
    s = data.get("summary", "Captured.")
    return (f"{s}. Logged {len(data.get('tasks', []))} tasks, "
            f"{len(data.get('todos', []))} to-dos, {len(data.get('knowledge', []))} notes, "
            f"{len(data.get('customers', []))} customer details.")


def _loads(text: str) -> dict:
    text = text.strip()
    if text.count("```") >= 2:
        text = text.split("```")[1]
        text = text[4:].strip() if text.lower().startswith("json") else text.strip()
    a, b = text.find("{"), text.rfind("}")
    try:
        return json.loads(text[a:b + 1])
    except Exception:  # noqa: BLE001
        return {"summary": "Could not parse capture.", "tasks": [], "todos": [],
                "knowledge": [], "customers": []}
