"""Per-customer / per-project context isolation — no cross-contamination.

You run many projects; their worlds must not bleed. Each customer gets an ISOLATED
workspace:
  vault/customers/<slug>/   tasks.md, todos.md, knowledge/, .customer.json, .session

Only the ACTIVE context is ever loaded into a turn. Switching customers also
switches the conversation thread (separate session) and the memory namespace, so
Jarvis never references one customer while you're working on another.

"general" = your personal/no-customer space (the vault root).
"""
import json
import re
from datetime import date

from . import config

VAULT = config.ROOT / "vault"
ACTIVE_FILE = VAULT / ".active"
GENERAL = "general"
_ALIASES = {"general", "personal", "none", "off", "me", "myself", "nobody"}


def _slug(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (name or "")).strip().replace(" ", "-")
    return (s[:60] or GENERAL).lower()


def active() -> str:
    if ACTIVE_FILE.exists():
        return (ACTIVE_FILE.read_text().strip() or GENERAL)
    return GENERAL


def workspace(slug: str | None = None):
    slug = slug or active()
    return VAULT if slug == GENERAL else VAULT / "customers" / slug


def switch(name: str) -> str:
    slug = GENERAL if (name or "").strip().lower() in _ALIASES else _slug(name)
    workspace(slug).mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(slug)
    return slug


def list_customers() -> list[str]:
    d = VAULT / "customers"
    return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.exists() else []


def memory_group(slug: str | None = None) -> str:
    return f"cust:{slug or active()}"


# -- per-customer conversation session (keeps dialogue threads separate) --------
def session_get(slug: str | None = None) -> str | None:
    p = workspace(slug) / ".session"
    return p.read_text().strip() if p.exists() else None


def session_set(sid: str | None, slug: str | None = None) -> None:
    if not sid:
        return
    p = workspace(slug) / ".session"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(sid)


# -- per-customer profile: who they are + how to communicate with them ----------
def _profile_path(slug: str | None = None):
    return workspace(slug) / ".customer.json"


def load_customer(slug: str | None = None) -> dict:
    p = _profile_path(slug)
    base = {"name": "", "comms": {}, "preferences": [], "dos": [], "donts": [],
            "notes": [], "links": {}}
    if p.exists():
        try:
            return {**base, **json.loads(p.read_text())}
        except Exception:  # noqa: BLE001
            pass
    return base


def save_customer(data: dict, slug: str | None = None) -> None:
    p = _profile_path(slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


# -- links: bind this context to the real project / conversation ---------------
# kinds: "code" = local Claude Code project dir (agent runs INSIDE it),
#        "cowork" = claude.ai / Claude-Code-on-web project URL,
#        "note" = freeform pointer to the conversation this is about.
def links(slug: str | None = None) -> dict:
    return load_customer(slug).get("links") or {}


def code_path(slug: str | None = None) -> str | None:
    return links(slug).get("code")


def set_link(kind: str, value: str, slug: str | None = None) -> None:
    c = load_customer(slug)
    c.setdefault("links", {})[kind] = value
    save_customer(c)


def prompt() -> str:
    """Injected per turn: the ACTIVE customer's context + a hard isolation rule."""
    slug = active()
    if slug == GENERAL:
        return ""
    c = load_customer(slug)
    name = c.get("name") or slug
    out = [f"\n\nACTIVE CUSTOMER: {name}.",
           "Stay STRICTLY within this customer's context. Never reference, reuse, "
           "or mix in any other customer's information, files, or history.",
           f"Scope all memory reads/writes to group '{memory_group(slug)}'."]
    comms = c.get("comms") or {}
    if comms:
        out.append("- Communicate as: " + ", ".join(f"{k}: {v}" for k, v in comms.items()))
    if c.get("preferences"):
        out.append("- Their preferences: " + "; ".join(c["preferences"]))
    if c.get("dos"):
        out.append("- Do: " + "; ".join(c["dos"]))
    if c.get("donts"):
        out.append("- Don't: " + "; ".join(c["donts"]))
    if c.get("notes"):
        out.append("- Notes: " + "; ".join(c["notes"]))
    lk = c.get("links") or {}
    if lk:
        bits = []
        if lk.get("code"):
            bits.append(f"local Claude Code project at {lk['code']} — you are working inside it")
        if lk.get("cowork"):
            bits.append(f"cowork/web project: {lk['cowork']}")
        if lk.get("note"):
            bits.append(lk["note"])
        out.append("- This chat is about (linked work): " + "; ".join(bits))
    return "\n".join(out)


# -- learn customer-specific facts / comms style from an utterance --------------
_client = None


def _client_get():
    global _client
    if _client is None:
        from anthropic import Anthropic
        _client = Anthropic()
    return _client


_TOOL = {
    "name": "update_customer",
    "description": "Record durable facts and communication preferences for THIS customer.",
    "input_schema": {
        "type": "object", "additionalProperties": False,
        "required": ["name", "comms", "preferences", "dos", "donts", "notes"],
        "properties": {
            "name": {"type": "string"},
            "comms": {"type": "object", "additionalProperties": {"type": "string"},
                      "description": "tone, formality, language, signature, channel, etc."},
            "preferences": {"type": "array", "items": {"type": "string"}},
            "dos": {"type": "array", "items": {"type": "string"}},
            "donts": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "array", "items": {"type": "string"}},
        },
    },
}


def learn(text: str) -> dict:
    """Extract durable facts + how-to-communicate for the ACTIVE customer."""
    c = load_customer()
    msg = _client_get().messages.create(
        model=config.MODEL_FAST,
        max_tokens=600,
        system=("Extract ONLY durable facts and communication preferences for the "
                f"current customer ('{c.get('name') or active()}'): tone/formality/"
                "language/signature/channel, do/don't, and key notes. Ignore one-off "
                "requests. Empty fields if nothing durable."),
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "update_customer"},
        messages=[{"role": "user", "content": text}],
    )
    delta = {}
    for b in msg.content:
        if getattr(b, "type", "") == "tool_use":
            delta = b.input
            break
    if delta.get("name") and not c.get("name"):
        c["name"] = delta["name"]
    for k, v in (delta.get("comms") or {}).items():
        c["comms"][k] = v
    for k in ("preferences", "dos", "donts", "notes"):
        for item in delta.get(k) or []:
            if item and item not in c[k]:
                c[k].append(item)
    save_customer(c)
    return delta
