"""Text-mode smoke test — prove the core loop without any voice/mic.

    py -m jarvis.chat              # interactive, model only (prove key -> Sonnet -> reply)
    py -m jarvis.chat --tools      # interactive, WITH the MCP tool loadout
    py -m jarvis.chat "one shot"   # single message and exit

Same brain as the voice app (model routing + self-escalation, approval gate,
per-customer context, personalization) — just typed in and printed out. The
fastest way to find what breaks before wiring the mic.
"""
import asyncio
import sys

from . import config, context
from .agent import run_turn


async def _once(text: str, bare: bool) -> None:
    print("[thinking…]")
    reply = await run_turn(text, bare=bare)
    print(f"\njarvis> {reply}\n")


async def _repl(bare: bool) -> None:
    mode = "model only" if bare else "with MCP tools"
    print(f"JARVIS text mode ({mode}) — fast={config.MODEL_FAST} heavy={config.MODEL_HEAVY}")
    print(f"context: {context.active()}   (type 'exit' or Ctrl-C to quit)\n")
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not text:
            continue
        if text.lower() in {"exit", "quit"}:
            return
        await _once(text, bare)


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--tools"]
    bare = "--tools" not in sys.argv          # default: model only
    if args:
        asyncio.run(_once(" ".join(args), bare))
    else:
        asyncio.run(_repl(bare))


if __name__ == "__main__":
    main()
