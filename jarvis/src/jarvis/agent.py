"""The brain: Claude Agent SDK wired to the MCP loadout + the approval gate.

NOTE: exact Agent SDK class/callback names can shift between versions — if an
import fails, check `claude-agent-sdk` docs and adjust. The shape is stable:
load MCP servers, pick a model per turn, gate outbound tools, stream the reply.
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


def _load_core_servers() -> dict:
    return json.loads(config.MCP_CORE.read_text()).get("mcpServers", {})


async def _can_use_tool(tool_name, tool_input, context=None):
    """Allow everything except outbound 'send' actions, which need a yes."""
    if requires_approval(tool_name, tool_input):
        if not await confirm(tool_name, tool_input):
            return PermissionResultDeny(message="User declined the outbound action.")
    return PermissionResultAllow()


async def run_turn(user_text: str) -> str:
    """Run one conversational turn; returns the text to speak."""
    options = ClaudeAgentOptions(
        model=choose_model(user_text),
        system_prompt=config.SYSTEM_PROMPT,
        mcp_servers=_load_core_servers(),
        allowed_tools=["mcp__*"],          # all MCP tools available...
        permission_mode="acceptAll",       # ...looser; the hook still gates sends
        can_use_tool=_can_use_tool,
    )

    out: list[str] = []
    async for message in query(prompt=user_text, options=options):
        text = getattr(message, "text", None) or getattr(message, "content", None)
        if isinstance(text, str):
            out.append(text)
    return "".join(out).strip()
