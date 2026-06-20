# The orb HUD

A dependency-free animated "Jarvis" orb. Open `index.html` in any browser
(or run it full-screen / always-on-top in a borderless window for the real look).

## How it's driven
- The backend (`src/jarvis/hud.py`, started by `main.py`) runs a WebSocket on
  `ws://localhost:8765` and broadcasts `{ "state": ..., "level": ... }`.
- The orb connects automatically and reacts:

| state | color | when |
|-------|-------|------|
| `idle` | teal | waiting for the wake word |
| `listening` | green | recording your voice |
| `thinking` | violet (extra rings) | Claude + tools are working |
| `speaking` | blue | TTS is talking |

- `level` (0–1) is an audio amplitude that pulses the orb. Hook it up in
  `voice.py` during record/playback for lip-sync-style reactivity (TODO).
- With no backend connected it runs a **demo cycle** so you can preview the look.

## Make it feel native (Windows)
- Open in a borderless/kiosk browser window, or wrap in a tiny Tauri/Electron
  always-on-top transparent overlay.
- Next upgrade: port the Three.js particle-orb from `ethanplusai/jarvis` here for
  a 3D version — this canvas orb is the lightweight stand-in.
