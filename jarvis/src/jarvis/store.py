"""The vault: where captured tasks / to-dos / knowledge land (local-first).

Plain Markdown so it's yours, greppable, and Obsidian-friendly. Nothing leaves
the machine by default; pushing into Graphiti memory or Notion via the agent is
an optional later step.
"""
from datetime import datetime

from . import config

VAULT = config.ROOT / "vault"


def _append(rel: str, text: str) -> None:
    p = VAULT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(text)


def _slug(s: str | None) -> str:
    s = "".join(c for c in (s or "") if c.isalnum() or c in " -_").strip()
    return (s[:50] or "note").replace(" ", "-").lower()


def save(data: dict) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    for t in data.get("tasks", []):
        due = f" (due {t['due']})" if t.get("due") else ""
        proj = f" #{_slug(t['project'])}" if t.get("project") else ""
        pri = t.get("priority", "med")
        _append("tasks.md", f"- [ ] {t.get('title', '(task)')}{due}{proj}  ~{pri}  <!-- {ts} -->\n")
    for td in data.get("todos", []):
        _append("todos.md", f"- [ ] {td}  <!-- {ts} -->\n")
    for k in data.get("knowledge", []):
        _append(f"knowledge/{_slug(k.get('topic'))}.md", f"\n## {ts}\n{k.get('note', '')}\n")
    for c in data.get("customers", []):
        _append("customers.md", f"- **{c.get('name', '?')}** — {c.get('detail', '')}  <!-- {ts} -->\n")
