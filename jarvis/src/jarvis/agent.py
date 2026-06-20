"""The brain: Claude Agent SDK (corrected to the real API) + MCP + approval gate.

Verified against the official Python SDK (claude-agent-sdk >= 0.2.x):
- Multi-turn via query() + session `resume` (so we can pick the model per turn,
  which is what makes routing + self-escalation work).
- permission_mode="default" so our can_use_tool callback actually runs.
- We deliberately do NOT set allowed_tools=["mcp__*"]: that wildcard AUTO-APPROVES
  every tool and would BYPASS the gate, so outbound 'send' tools would never be
  caught. Instead every tool flows through can_use_tool, which allows everything
  except outbound sends (those ask for approval).
- Messages are typed objects: AssistantMessage.content -> [TextBlock, ToolUseBlock],
  end-of-turn is ResultMessage (carries session_id, cost).
"""
import json

from claude_agent_sdk import (  # type: ignore
    AssistantMessage,
    ClaudeAgentOptions,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
    query,
)

from . import config, context, profile
from .approval import confirm, is_destructive, requires_approval
from .router import choose_model

_ESCALATE_HINT = (
    "\n\nESCALATION: If this needs deep reasoning (hard coding, multi-step "
    "research, tricky planning/debugging), do not attempt it now — reply with "
    "exactly 'ESCALATE: <one-line reason>' and nothing else. Otherwise answer "
    "normally."
)


def _servers() -> dict:
    # .mcp.json wraps servers under "mcpServers"; the SDK wants the inner mapping.
    return json.loads(config.MCP_CORE.read_text()).get("mcpServers", {})


async def _can_use_tool(tool_name: str, input_data: dict, context=None):
    """Allow everything except outbound sends + catastrophic commands (ask first)."""
    if requires_approval(tool_name, input_data) or is_destructive(tool_name, input_data):
        if await confirm(tool_name, input_data):
            return PermissionResultAllow()
        return PermissionResultDeny(message=f"User declined '{tool_name}'.")
    return PermissionResultAllow()


async def _ask(prompt: str, model: str, allow_escalate: bool, bare: bool = False) -> str:
    sid = context.session_get()          # conversation is scoped per customer
    kwargs = dict(
        model=model,
        system_prompt=(config.SYSTEM_PROMPT + profile.prompt() + context.prompt()
                       + (_ESCALATE_HINT if allow_escalate else "")),
        mcp_servers=({} if bare else _servers()),
        permission_mode="default",       # so can_use_tool is actually invoked
        can_use_tool=_can_use_tool,
        max_turns=15,                     # cap the agent loop (runaway-cost guard)
    )
    if sid:
        kwargs["resume"] = sid           # continue THIS customer's conversation
    code = context.code_path()           # if linked to a Claude Code project,
    if code:                             # run INSIDE it (its files, CLAUDE.md, MCP)
        kwargs["cwd"] = code
        kwargs["setting_sources"] = ["project"]
    options = ClaudeAgentOptions(**kwargs)

    parts: list[str] = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    parts.append(block.text)
        elif isinstance(message, ResultMessage):
            context.session_set(getattr(message, "session_id", None))
    return "".join(parts).strip()


async def run_turn(user_text: str, bare: bool = False) -> str:
    """Sonnet by default; Opus for heavy work or when Sonnet escalates itself.

    bare=True runs the model with NO MCP servers (for the text-mode smoke test).
    NOTE: the escalation triage shares the session, so the brief 'ESCALATE:' turn
    lands in history. Fine for a scaffold; a tool-based handoff would be cleaner.
    """
    model = choose_model(user_text)

    if model == config.MODEL_FAST and config.MODEL_HEAVY != config.MODEL_FAST:
        reply = await _ask(user_text, config.MODEL_FAST, allow_escalate=True, bare=bare)
        if reply.upper().startswith("ESCALATE:"):
            reason = reply.split(":", 1)[1].strip()
            print(f"[router] Sonnet -> Opus  ({reason})")
            return await _ask(user_text, config.MODEL_HEAVY, allow_escalate=False, bare=bare)
        return reply

    return await _ask(user_text, model, allow_escalate=False, bare=bare)
