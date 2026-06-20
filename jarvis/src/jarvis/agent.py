"""The brain: Claude Agent SDK + MCP loadout + approval gate + self-escalation.

Routing:
- `choose_model()` sends obviously-heavy turns straight to Opus.
- For everything else Sonnet runs, but with an escape hatch: if it decides the
  task needs deeper reasoning it answers `ESCALATE: <reason>` and the turn is
  re-run on Opus. So Jarvis can upgrade its own brain mid-task.

NOTE: exact Agent SDK names can shift between versions — if an import fails,
check `claude-agent-sdk` and adjust. The shape is stable.
"""
import json

from claude_agent_sdk import (  # type: ignore
    ClaudeAgentOptions,
    PermissionResultAllow,
    PermissionResultDeny,
    query,
)

from . import config
from .approval import confirm, requires_approval
from .router import choose_model

_ESCALATE_HINT = (
    "\n\nESCALATION: If this request needs deep reasoning (hard coding, "
    "multi-step research, tricky planning or debugging), do not attempt it now — "
    "reply with exactly 'ESCALATE: <one-line reason>' and nothing else. "
    "Otherwise just answer normally."
)


def _load_core_servers() -> dict:
    return json.loads(config.MCP_CORE.read_text()).get("mcpServers", {})


async def _can_use_tool(tool_name, tool_input, context=None):
    """Allow everything except outbound 'send' actions, which need a yes."""
    if requires_approval(tool_name, tool_input):
        if not await confirm(tool_name, tool_input):
            return PermissionResultDeny(message="User declined the outbound action.")
    return PermissionResultAllow()


async def _run(prompt: str, model: str, allow_escalate: bool) -> str:
    options = ClaudeAgentOptions(
        model=model,
        system_prompt=config.SYSTEM_PROMPT + (_ESCALATE_HINT if allow_escalate else ""),
        mcp_servers=_load_core_servers(),
        allowed_tools=["mcp__*"],
        permission_mode="acceptAll",   # looser; the hook still gates outbound sends
        can_use_tool=_can_use_tool,
    )
    out: list[str] = []
    async for message in query(prompt=prompt, options=options):
        text = getattr(message, "text", None) or getattr(message, "content", None)
        if isinstance(text, str):
            out.append(text)
    return "".join(out).strip()


async def run_turn(user_text: str) -> str:
    """Run one turn. Sonnet by default; Opus for heavy work or on self-escalation."""
    model = choose_model(user_text)

    # Borderline turn: let Sonnet decide if it needs Opus.
    if model == config.MODEL_FAST and config.MODEL_HEAVY != config.MODEL_FAST:
        reply = await _run(user_text, config.MODEL_FAST, allow_escalate=True)
        if reply.upper().startswith("ESCALATE:"):
            reason = reply.split(":", 1)[1].strip()
            print(f"[router] Sonnet -> Opus  ({reason})")
            return await _run(user_text, config.MODEL_HEAVY, allow_escalate=False)
        return reply

    return await _run(user_text, model, allow_escalate=False)
