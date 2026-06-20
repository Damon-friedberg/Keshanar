# JARVIS — a Claude-powered voice assistant for Windows

A "do everything while you talk to it" desktop assistant: wake on a double-clap,
talk back and forth out loud, control the whole machine, see your Claude Code
projects, run errands across your apps, and deliver a spoken morning briefing.

> **Status: scaffold.** This is a runnable skeleton with the architecture wired
> and clearly marked `TODO`s where your machine, mic, and API keys plug in. It is
> built to be filled in incrementally, not to run perfectly on first clone.

## The stack

```
Wake (double-clap)
  -> STT (faster-whisper, local)
    -> Claude Agent SDK   [router: Sonnet for chat, Opus for heavy work]
       + MCP tools (control + apps + memory)
    -> TTS (ElevenLabs Flash)
  -> Orb UI (ported from the reference build)
```

- **Brain:** Claude Agent SDK. `JARVIS_MODEL_FAST` handles live conversation;
  `JARVIS_MODEL_HEAVY` auto-engages for coding / research / planning. Set the
  exact model IDs in `.env` (the current Sonnet and Opus 4.x IDs).
- **Base it borrows from:** `Julian-Ivanov/jarvis-voice-assistant` (Windows,
  Claude, double-clap, orb, MIT). The prettier Three.js particle orb is ported
  from `ethanplusai/jarvis` later (see `ui/`).

## The tool loadout (`.mcp.json`)

| Group | Server | Gives Jarvis |
|-------|--------|--------------|
| Control | **Desktop Commander** | terminal + read/write/edit any file (also reads your local Claude Code projects) |
| Control | **Terminator** | native Windows GUI control (click/type in any app) |
| Control | **Playwright MCP** | full browser control |
| Apps | **Composio** | ~500 apps / 20k actions (Slack, Gmail, Calendar, Notion, WhatsApp…) behind one endpoint |
| Code | **Serena** | symbol-level intelligence over big codebases |
| Memory | **Graphiti** | temporal knowledge graph (what's true *and when it changed*) |
| Recall | **Screenpipe** | 24/7 local screen+audio history, queryable |
| Web | **Exa** | live semantic web search |

Everything else (Blender, Unity/Godot, RE tooling, the other 600 MCPs) lives
behind an MCP **gateway** and loads on demand — not always-on, to avoid tool
bloat. See `docs` notes in `config.py`.

## Security posture (as configured)

Looser / full control — **with one hard gate: nothing is *sent* to anyone
without your explicit approval.** Outbound actions (message / email / post / DM)
are intercepted in `approval.py`; everything else runs without prompting.
Change the patterns in `approval.py` to widen or narrow the gate.

## Setup (Windows)

```powershell
# 1. Python deps
py -m venv .venv; .\.venv\Scripts\activate
pip install -r requirements.txt

# 2. Node tools used by several MCP servers
#    (Desktop Commander, Terminator, Playwright, Screenpipe run via npx)
#    Install Node.js LTS first, then they auto-fetch on first run.

# 3. Keys
copy .env.example .env   # then fill in ANTHROPIC_API_KEY, ELEVENLABS_API_KEY, etc.

# 4. Run
py -m jarvis.main
```

## Use these MCPs in Claude Code too

Jarvis and Claude Code share the exact same tool loadout.

- **Quickest:** run Claude Code from the `jarvis/` folder — it auto-loads
  `.mcp.json` (project scope), so the core 12 are instantly available.
- **Everywhere:** register them at user scope so *every* Claude Code session has
  them:
  ```powershell
  .\scripts\setup_claude_code.ps1     # adds the core to Claude Code (user scope)
  claude mcp list                     # verify
  ```
- **The full catalog too:** add the gateway as ONE entry so Claude Code reaches
  every bundle without tool-bloat — see `config/GATEWAY.md`.

> Adding all ~50 catalog servers directly to Claude Code bloats it the same way
> it would bloat Jarvis. **Core direct + catalog-via-gateway** is the sane setup
> for both.

## Overnight briefing

`briefing.py` is meant to be run unattended (Claude Code Routines in the cloud,
or Windows Task Scheduler locally). It gathers overnight context and writes
`briefing.md`; a wake-time job reads it aloud. See `scripts/schedule_briefing.ps1`.

## Self-improvement

Jarvis writes reusable playbooks it learns into `skills/`. The nightly briefing
includes a short reflection step that proposes new skills. This is the safe,
lightweight alternative to bolting on a "self-evolving agent" framework.
