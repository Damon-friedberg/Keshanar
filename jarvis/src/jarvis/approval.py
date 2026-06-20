"""Gates that run OUTSIDE the model's control (platform-layer, per production
postmortems — models talk their way past prompt-only rules):

1. Outbound sends (message/email/post/DM) -> always ask. (Your one hard gate.)
2. Catastrophic commands (rm -rf ~, format, DROP DATABASE, git push --force...)
   -> ask. This protects your machine from the AGENT'S mistakes, not from
   attackers; toggle off with JARVIS_GUARD_DESTRUCTIVE=0 if you want it fully loose.
"""
import os
import re

# Tool-name fragments that mean "this leaves the machine toward a person".
_OUTBOUND = [
    r"send", r"\bpost\b", r"message", r"\bemail\b", r"\bmail\b", r"reply",
    r"\bdm\b", r"tweet", r"publish", r"broadcast", r"\bchat[_.]?post",
    r"create_?message", r"compose", r"share", r"comment",
]
_OUTBOUND_RE = re.compile("|".join(_OUTBOUND), re.I)

# Never gate these even if they match (read-only lookups, drafts).
_SAFE = re.compile(r"(search|list|get|read|fetch|draft|preview|history)", re.I)


def requires_approval(tool_name: str, tool_input: dict | None = None) -> bool:
    name = (tool_name or "").lower()
    if _SAFE.search(name) and not re.search(r"send|post|publish", name):
        return False
    return bool(_OUTBOUND_RE.search(name))


_GUARD = os.getenv("JARVIS_GUARD_DESTRUCTIVE", "1") != "0"
_DESTRUCTIVE = re.compile(
    r"""rm\s+-rf?\s+[~/]      # rm -rf / or ~
      | \bdel\s+/[sfq]        # del /s /f /q
      | \brmdir\s+/s
      | format\s+[a-z]:       # format c:
      | \bmkfs\b | \bdd\s+if=
      | git\s+push\s+.*--force
      | \bdrop\s+(table|database)\b
      | :\(\)\s*\{            # fork bomb
    """,
    re.I | re.X,
)


def is_destructive(tool_name: str, tool_input: dict | None = None) -> bool:
    if not _GUARD:
        return False
    blob = " ".join(str(v) for v in (tool_input or {}).values())
    return bool(_DESTRUCTIVE.search(blob))


async def confirm(tool_name: str, tool_input: dict | None = None) -> bool:
    """Ask the user to approve an outbound action.

    TODO: in the voice app, speak this and listen for a yes/no instead of stdin.
    """
    print(f"\n[APPROVAL NEEDED] Jarvis wants to: {tool_name}")
    if tool_input:
        print(f"  payload: {tool_input}")
    try:
        return input("  Approve? [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False
