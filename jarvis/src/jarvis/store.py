"""The vault: captured tasks / to-dos / knowledge, isolated PER ACTIVE CONTEXT.

Tasks/todos/knowledge land in the active customer's workspace (or the general
vault) so projects never cross-contaminate. The customers/ registry stays global.
Obsidian-native (frontmatter, [[wikilinks]], Tasks dates) + idempotent dedup.
"""
import hashlib
import re
from datetime import date, datetime

from . import context

_PRI = {"high": "🔼", "med": "", "low": "🔽"}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", (s or "").lower())).strip()


def _bid(kind: str, text: str) -> str:
    return f"{kind[0]}-{hashlib.sha1(_norm(text).encode()).hexdigest()[:8]}"


def _slug(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (s or "")).strip().replace(" ", "-")
    return (s[:60] or "note").lower()


def _link(name: str | None) -> str:
    return f"[[{name}]]" if name else ""


def _read(rel: str) -> str:
    p = context.workspace() / rel               # active context workspace
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _append(rel: str, text: str) -> None:
    p = context.workspace() / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(text)


def _touch_customer(name: str, detail: str | None = None) -> None:
    # The customers/ registry is GLOBAL (not per-workspace).
    p = context.VAULT / "customers" / f"{_slug(name)}.md"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"---\ntype: customer\nname: {name}\ntags: [customer]\n"
                     f"created: {date.today().isoformat()}\n---\n# {name}\n\n## Details\n",
                     encoding="utf-8")
    if detail and _norm(detail) not in _norm(p.read_text(encoding="utf-8")):
        with p.open("a", encoding="utf-8") as f:
            f.write(f"- {datetime.now():%Y-%m-%d %H:%M}: {detail}\n")


def save(data: dict) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    tasks_md = _read("tasks.md")
    for t in data.get("tasks", []):
        bid = _bid("task", t.get("title", ""))
        if bid in tasks_md:                       # idempotent dedup
            continue
        line = [f"- [ ] {t.get('title', '(task)')}"]
        if t.get("customer"):
            line.append(f"[customer:: {_link(t['customer'])}]")
        if t.get("project"):
            line.append(f"[project:: {_link(t['project'])}]")
        if _PRI.get(t.get("priority") or "med"):
            line.append(_PRI[t["priority"]])
        if t.get("due"):
            line.append(f"📅 {t['due']}")
        line.append(f"^{bid}")
        _append("tasks.md", " ".join(line) + "\n")
        if t.get("customer"):
            _touch_customer(t["customer"])

    todos_md = _read("todos.md")
    for td in data.get("todos", []):
        bid = _bid("todo", td)
        if bid not in todos_md:
            _append("todos.md", f"- [ ] {td} ^{bid}\n")

    for k in data.get("knowledge", []):
        rel = f"knowledge/{_slug(k.get('topic'))}.md"
        if not (context.workspace() / rel).exists():
            cust = f'\ncustomer: "{_link(k["customer"])}"' if k.get("customer") else ""
            _append(rel, f"---\ntype: knowledge\ntopic: {k.get('topic', 'note')}\n"
                         f"tags: [knowledge]\nsource: capture\ncreated: {date.today().isoformat()}{cust}\n---\n")
        note = k.get("note", "")
        if _norm(note) not in _norm(_read(rel)):
            _append(rel, f"\n- {ts}: {note}\n")
        if k.get("customer"):
            _touch_customer(k["customer"])

    for c in data.get("customers", []):
        _touch_customer(c.get("name", "?"), c.get("detail", ""))
