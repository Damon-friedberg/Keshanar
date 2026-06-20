"""Overnight briefing: gather context unattended, write briefing.md, optionally
speak it at wake time.

Designed to be run headless by Claude Code Routines (cloud, runs with your PC
off) or Windows Task Scheduler. See scripts/schedule_briefing.ps1.

    py -m jarvis.briefing            # generate + save
    py -m jarvis.briefing --speak    # generate + read it aloud
"""
import asyncio
import sys

from . import config, voice
from .agent import run_turn

BRIEFING_PROMPT = """Produce my morning briefing. Use your tools to gather:
- today's calendar and any new important email (via the apps tools),
- what I worked on yesterday (via the screen-recall / memory tools),
- 3-5 relevant news or research items (via web search),
- any follow-ups or TODOs you remember for me.

Then write a tight, friendly spoken-style summary (under ~200 words). End with
one suggested focus for the day. Save nothing that needs sending; just report.
"""


async def generate(speak_it: bool = False) -> str:
    text = await run_turn(BRIEFING_PROMPT)
    config.BRIEFING_FILE.write_text(text, encoding="utf-8")
    print(f"[briefing] written to {config.BRIEFING_FILE}")
    if speak_it:
        voice.speak("Good morning. Here is your briefing. " + text)
    return text


if __name__ == "__main__":
    asyncio.run(generate(speak_it="--speak" in sys.argv))
