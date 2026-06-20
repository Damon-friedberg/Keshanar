# JARVIS — self-evaluation, rating & roadmap

Honest assessment of the scaffold as it stands. Scores are /10. The headline:
**the design is strong and complete; almost nothing has been validated on real
Windows hardware yet.** That gap is the whole story.

## Scorecard

| Dimension | Score | Notes |
|---|---|---|
| Architecture & design | 9 | Lean always-on core + on-demand catalog behind a gateway is the right call; cleanly separated modules. |
| Model routing | 8 | Sonnet default, Opus for heavy, **plus genuine self-escalation**. The escalation is a text-protocol (`ESCALATE:`) — works, but a tool-based handoff would be cleaner. |
| Voice I/O | 5 | Real libraries wired (faster-whisper, ElevenLabs, pyttsx3 fallback) but **wake word is a stub** and nothing is mic-tested. No barge-in / streaming yet. |
| Computer control & tools | 7 | Strong, verified core (Desktop Commander, Terminator, Playwright, Composio, Serena). A few server launch commands are best-effort and **unverified** (graphiti, screenpipe pkg, composio flow). |
| Memory & recall | 6 | Graphiti + Screenpipe chosen well, but neither is wired into the loop or proven; Graphiti needs Neo4j. |
| Overnight briefing | 6 | Sound pattern (Routines/Task Scheduler -> file -> TTS) but unproven end-to-end. |
| Orb HUD | 8 | Real, dependency-free, reactive to live state; looks good. Not yet the 3D particle version; `level` not yet fed from audio. |
| Security / safety | 5 | Matches the requested "looser" posture with an outbound-send gate — but full computer control + always-listening is a **large prompt-injection blast radius**, and only sends are gated. Deliberate, but it's the biggest real risk. |
| Setup & DX | 7 | `doctor.py`, Claude Code setup scripts, `.env.example`, clear README. No installer; first-run will still have rough edges. |
| Verification / reliability | 5 | Every module imports against the *real* `claude-agent-sdk` (SDK API confirmed correct); deterministic core (routing, send/destructive gates, context isolation+linking, dedup) has a passing `pytest` suite. Not yet run live (needs your API key) or on voice/screen hardware. |

**Overall: 7/10 as a scaffold** — excellent bones, fast path to a real demo,
but it's a blueprint with stubs, not a proven app. The 7 reflects design quality;
the 3 in verification is the honest anchor.

## What would actually make it better (prioritized)

### P0 — prove it runs (turn the 3 into a 7)
1. **Validate the Agent SDK wiring** against the installed `claude-agent-sdk`
   version: one text-mode turn, Sonnet, one tool call. Fix any API drift.
2. **Verify each core MCP server launches** (`claude mcp list` + a call each).
   Drop or fix any that don't (likely: graphiti, screenpipe, composio flow).
3. **`doctor.py` deeper** — actually ping each server and report up/down.

### P1 — make it feel like the videos
4. **Real double-clap wake** + mic test; text-mode fallback already exists.
5. **Streaming TTS + barge-in** (interrupt Jarvis mid-sentence) for low latency.
6. **Feed `level` to the orb** from the audio stream (real-time reactivity), and
   port the 3D Three.js particle orb.
7. **Wire memory**: pick Graphiti *or* basic-memory, store/recall preferences,
   and have the nightly briefing write `skills/` entries (the self-improve loop).

### P2 — make it safe enough to trust with full control
8. **Tiered gates beyond sends**: confirm on destructive shell/file ops and
   `rm`/registry/writes outside an allowlisted set of folders.
9. **Run `mcp-scan`** over the config; pin server versions; isolate each via the
   gateway/containers.
10. **Tests + CI**, and verify any long-tail catalog server before trusting it.

## The single most important next step
Get **one real end-to-end turn** working (wake -> STT -> Sonnet -> a tool ->
TTS) on the actual machine. Everything else is polish on top of that proof.
