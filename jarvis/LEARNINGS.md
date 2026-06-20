# What we learned from other people's assistants — and what we changed

We studied the strongest reference projects in each pillar and ported the lessons.
✅ = applied to the code now. ⏳ = on the roadmap (EVALUATION.md).

## Agent / Claude SDK  — refs: anthropics/claude-agent-sdk, OpenClaw
- ✅ **Use the real SDK API.** `ClaudeAgentOptions` + `query()` with session `resume`
  for multi-turn; typed messages (`AssistantMessage`/`TextBlock`/`ResultMessage`).
- ✅ **Fixed a real bug:** `allowed_tools=["mcp__*"]` auto-approves every tool and
  *bypasses the approval callback* — so the "don't send without asking" gate would
  never have fired. Removed it; everything now flows through `can_use_tool` under
  `permission_mode="default"`. (`acceptAll` isn't even a valid mode.)
- ✅ **Cap the loop:** `max_turns=15`. Postmortems show runaway loops burning
  thousands of dollars in minutes. [answer.ai, inkog.io]
- ⏳ Repeated-tool-call detector; context sliding-window + summarize (context
  overflow is cited as ~80% of agent failures); prompt-caching the stable prefix.

## Voice loop — refs: Pipecat, LiveKit, VoiceMode, Vocode, ethanplusai
- ✅ **VAD endpointing** (record-until-silence via webrtcvad, ~1s hangover) instead
  of a fixed N-second record. This is the single biggest "feel" win; every mature
  loop does it. (Pipecat `stop_secs=0.8`, LiveKit `min_endpointing_delay=500ms`.)
- ✅ **TTS fallback** (ElevenLabs → offline pyttsx3) — OpenClaw flags cloud-TTS as a
  single point of failure; never have only one voice path.
- ⏳ **Barge-in** (interrupt TTS mid-sentence): run playback on its own task with a
  stop-event, keep a VAD listener live while speaking, `min_interruption_duration
  ≈0.5s` to ignore coughs. Pattern: ethanplus does client-stop + server-cancel.
- ⏳ **Sentence-streamed LLM→TTS** (speak the first sentence while the model is still
  generating) — collapses time-to-first-audio. Needs `run_turn` to yield deltas.
- ⏳ Real wake word (openWakeWord / Porcupine) replacing the double-clap TODO.
- ⏳ Echo handling: half-duplex + 300ms guard after TTS before re-arming the mic.

## Capture → tasks/knowledge — refs: Screenpipe, Khoj, PKM/extraction guides
- ✅ **Schema-guaranteed extraction** via forced tool-use (`record_capture`) instead
  of "respond with JSON" + brace-scraping — kills the silent-empty-capture failure.
- ✅ **Precision prompt:** extract only what's grounded; never invent due dates;
  empty lists over padding (a wrong task is worse than a missed one).
- ✅ **Idempotent dedup** (block-id per item) so re-capturing doesn't duplicate.
- ✅ **Obsidian-native vault:** frontmatter, `[[wikilinks]]`, Tasks-plugin dates,
  per-customer notes → actually retrievable later, not a flat log.
- ✅ **Light PII redaction** on narration before it leaves the machine.
- ✅ **On-demand vision only** (already): a screenshot in context is re-billed every
  turn (~25× the text cost) — capture deliberately, don't watch every turn.
- ⏳ Human-in-the-loop inbox; lean on Screenpipe's timeline for always-on recall.

## Safety with full computer control — refs: OpenClaw, steipete, postmortems
- ✅ **Platform-layer gates, not prompt rules** (models talk past prompt rules):
  outbound sends + catastrophic commands (`rm -rf ~`, `format`, `DROP DATABASE`,
  `git push --force`) ask first. Toggle with `JARVIS_GUARD_DESTRUCTIVE=0`.
- ⏳ **Treat screen/web text as untrusted data, not instructions** (indirect prompt
  injection is the #1 threat for a screen-reading agent) — adopt plan-then-execute
  / dual-LLM for captured content. [arxiv 2506.08837, OWASP LLM01]
- ⏳ **Sandbox** computer-control tools for any session that ingests external content
  (OpenClaw's deny-by-default Docker model); flagship model for tool dispatch.
- ⏳ Automated hourly workspace snapshot + restore path (steipete's YOLO mitigation).

## Architecture & ops — refs: Leon, Khoj, OpenClaw, builder writeups
- ✅ **doctor preflight** (already) — both OpenClaw and GitLab's `doctor` pattern.
- ✅ **Model routing** Sonnet→Opus with self-escalation (ethanplus's Haiku/Opus split).
- ⏳ **Don't over-engineer** — the #1 documented regret. Prove one vertical slice
  before adding layers. (We're guilty of building wide; see process eval.)
- ⏳ Retry-with-backoff (only on 429/5xx/timeout; idempotent tools, never re-run a
  tool that mutated state); structured traces (tokens/latency/cost per call);
  provider/model failover; per-session token+$ budget with hard stop.
- ⏳ pydantic-settings config; plugin/skill system via entry points; real tests with
  an injectable fake LLM client + record/replay cassettes.
- ⚠️ **Cautionary tales:** Leon's single fragile Python bridge (froze the whole app);
  Khoj's mandatory local embedding model that OOMs. Keep components decoupled and
  degrade gracefully.

## Sources
Full source URLs are in the research notes; key ones:
code.claude.com/docs/en/agent-sdk · github.com/pipecat-ai/pipecat ·
docs.livekit.io/agents · github.com/mbailey/voicemode · github.com/openclaw/openclaw ·
platform.claude.com/docs/en/build-with-claude/structured-outputs · arxiv.org/abs/2506.08837 ·
answer.ai/posts/2026-01-20-toolcalling.html · github.com/leon-ai/leon · github.com/khoj-ai/khoj
