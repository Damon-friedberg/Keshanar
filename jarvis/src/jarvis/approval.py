"""The one hard gate: nothing gets SENT to anyone without approval.

Everything else runs without prompting (looser / full-control posture).
Widen or narrow the patterns below to taste.
"""
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
