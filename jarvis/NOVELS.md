# Jarvis for novels — writing & editing at a high level

Your per-customer isolation maps perfectly onto **one context per manuscript**, and
the memory stack *is* the product: continuity is a novel's hardest problem, and a
temporal knowledge graph solves exactly it.

## The stack (bundle: `config/mcp_catalog/novel_writing.json`)
- **Graphiti** — continuity engine. Temporal knowledge graph: facts with validity
  windows, so *"what does Sarah know about the murder as of ch.12?"* respects the
  timeline. The continuity sentinel. (Core; needs Neo4j + a key.)
- **Obsidian** — your story bible / world wiki; Claude reads *and writes* it.
- **Adeu** — line edits as native **Word tracked changes** (accept/reject like a
  real edit pass).
- **ElevenLabs** — hear prose **read aloud**; catch rhythm the eye misses.
- **MarkItDown** — DOCX / Scrivener / PDF ↔ markdown so AI edits the real file.
- **Exa** — deep research / fact-checking. (Core.)
- **Google Workspace** — optional, if the manuscript lives in Google Docs.

## Setup (do once)
1. **Graphiti backend:** `docker run -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/yourpass neo4j`
   then set `NEO4J_URI/USER/PASSWORD` in `.env`.
2. **Obsidian:** install the *Local REST API* community plugin in your vault, copy
   its key into `OBSIDIAN_API_KEY` (+ `OBSIDIAN_HOST`, e.g. `https://127.0.0.1:27124`).
3. **Keys:** `ELEVENLABS_API_KEY`, `EXA_API_KEY` in `.env`.
4. Register the bundle (or load it through the gateway — see `config/GATEWAY.md`).

## The workflow
1. **One context per book.** Say *"work on Nightshade"* → isolated context (its own
   memory, tasks, conversation). `link this to D:\manuscripts\nightshade` so Jarvis
   works inside the manuscript folder. No bleed between books.
2. **Story bible lives in Obsidian.** Characters, timeline, world rules, voice notes.
   Jarvis updates it as you draft; it's the human-readable mirror of the Graphiti graph.
3. **Continuity sentinel.** Ingest new pages into Graphiti; ask *"any contradictions
   in the last chapter — eye colour, who-knew-what-when, timeline?"* This is the
   killer feature of the memory stack for long-form/series.
4. **Dictation mode.** Talk a scene; it drafts into the manuscript (your STT already
   does this). Many working novelists dictate.
5. **Read-back editing.** *"Read me that paragraph"* → ElevenLabs speaks it; you hear
   the clunk.
6. **Editor mode.** Line edits come back as **tracked changes** (Adeu) on the DOCX.
7. **Per-book morning briefing.** `briefing.py` pointed at the active book: *"here's
   where you left off, the open threads, and two continuity flags."*

## Note on long manuscripts
A 120k-word novel doesn't fit in context — that's *why* the memory stack matters.
The pattern is: work chapter/scene-scoped, keep the **story bible (Obsidian) +
continuity graph (Graphiti)** as the durable source of truth, and retrieve the
relevant slice per turn rather than stuffing the whole book in.
