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

# 4. Preflight, then run
py -m jarvis.doctor        # checks keys, CLIs, MCP config
py -m jarvis.main

# 5. (optional) open the orb HUD in a browser
start ui\orb\index.html
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

## Capture: talk + show your screen → tasks, to-dos, knowledge

Talk out loud while showing Jarvis your screen (customers, work, what you need to
do); it watches **and** listens, then compiles everything into structured items.

- Say **"start capture"** for a walkthrough — narrate step by step, Jarvis grabs
  the screen each time, say **"done"** and it compiles one tidy set.
- Say **"capture this" / "log this" / "make tasks"** for a single screen+voice
  snapshot.

Everything lands locally in `vault/`: `tasks.md`, `todos.md`, `customers.md`, and
`knowledge/<topic>.md`. Nothing is sent anywhere. (Optional next step: push these
into Graphiti memory or Notion via the agent.)

## One project at a time — zero cross-contamination

You run many projects; their worlds must never bleed together. Each customer gets
an **isolated workspace** (`vault/customers/<name>/`) with its own tasks, knowledge,
communication style, **conversation thread**, and memory namespace. Only the
**active** context is ever loaded into a turn.

- **Switch:** *"work on Acme"* / *"switch to Beta"* → from then on, tasks, captures,
  learning, and the conversation are scoped to that customer. *"switch to personal"*
  resets. Each customer keeps its own dialogue thread, so Jarvis never references
  Beta while you're on Acme.
- **Per-customer comms:** while on a customer, *"remember to always be formal with
  them and sign as Damon"* updates **that customer's** profile (tone, formality,
  signature, channel) — not your personal one. Jarvis then communicates in their
  custom style.
- **Link it to the real work:** *"link this to C:\\dev\\acme-site"* binds the
  context to a **local Claude Code project** — Jarvis then runs **inside** that
  folder (its files, `CLAUDE.md`, and MCP servers), so the chat is tied to the
  actual codebase. *"link this to https://claude.ai/project/…"* records the
  **cowork / web** project so it knows where the canonical conversation lives.

## Learns you & adapts

Jarvis gets to know you and tailors itself over time — two tiers:

- **Profile** (`profile.py` → `vault/profile.md`): a compact summary of your
  identity, preferences, communication style, the people and projects in your
  world, and your do's/don'ts. It's injected into **every turn**, so Jarvis adapts
  immediately. Say things like *"call me Cap,"* *"I prefer short answers,"* *"from
  now on default to metric,"* *"remember Dana is the Acme contact"* — it captures
  them on the spot. Corrections stick too.
- **Deep memory** (Graphiti / basic-memory MCP): the evolving, time-aware
  knowledge graph the agent reads/writes via tools for the long tail — *what's true
  and when it changed.*
- **Consolidation:** the nightly briefing reflects on the day and updates both,
  and successful workflows get written to `skills/`.

Your profile lives in `vault/` (gitignored — it never leaves your machine).

## Overnight briefing

`briefing.py` is meant to be run unattended (Claude Code Routines in the cloud,
or Windows Task Scheduler locally). It gathers overnight context and writes
`briefing.md`; a wake-time job reads it aloud. See `scripts/schedule_briefing.ps1`.

## Self-improvement

Jarvis writes reusable playbooks it learns into `skills/`. The nightly briefing
includes a short reflection step that proposes new skills. This is the safe,
lightweight alternative to bolting on a "self-evolving agent" framework.
