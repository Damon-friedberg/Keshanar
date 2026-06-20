"""Preflight check:  py -m jarvis.doctor   (add --ping for a live model call)

Verifies Python, packages, API keys, CLIs, audio devices, MCP config, and the
active context — so you know exactly what's missing before the first run.
"""
import importlib.util
import json
import os
import shutil
import sys

from . import config, context


def _mark(ok: bool) -> str:
    return "OK  " if ok else "MISS"


def _has(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:  # noqa: BLE001
        return False


def main() -> None:
    print("JARVIS doctor\n=============")
    print(f"[{_mark(sys.version_info >= (3, 11))}] python {sys.version.split()[0]} (need >=3.11)")

    for mod, label in [("anthropic", "anthropic"), ("claude_agent_sdk", "claude-agent-sdk"),
                       ("dotenv", "python-dotenv"), ("faster_whisper", "faster-whisper (voice)"),
                       ("sounddevice", "sounddevice (voice)"), ("webrtcvad", "webrtcvad (voice VAD)"),
                       ("mss", "mss (screen capture)")]:
        print(f"[{_mark(_has(mod))}] pkg {label}")

    print(f"[{_mark(bool(os.getenv('ANTHROPIC_API_KEY')))}] env ANTHROPIC_API_KEY (required)")
    for k in ("ELEVENLABS_API_KEY", "COMPOSIO_API_KEY", "EXA_API_KEY",
              "FIRECRAWL_API_KEY", "CONTEXT7_API_KEY", "GITHUB_TOKEN"):
        print(f"[{'ok  ' if os.getenv(k) else '--  '}] env {k} (optional)")

    for cli in ("npx", "uvx", "claude"):
        print(f"[{_mark(bool(shutil.which(cli)))}] cli {cli}")

    try:
        import sounddevice as sd
        devs = sd.query_devices()
        ins = sum(1 for d in devs if d.get("max_input_channels", 0) > 0)
        outs = sum(1 for d in devs if d.get("max_output_channels", 0) > 0)
        print(f"[{_mark(ins > 0 and outs > 0)}] audio  {ins} input / {outs} output devices")
    except Exception as e:  # noqa: BLE001
        print(f"[--  ] audio  (couldn't query: {e})")

    placeholder = "-x" in config.MODEL_FAST or "-x" in config.MODEL_HEAVY
    print(f"[{_mark(not placeholder)}] models fast={config.MODEL_FAST} heavy={config.MODEL_HEAVY}"
          + ("   <- set real IDs in .env" if placeholder else ""))
    try:
        servers = json.loads(config.MCP_CORE.read_text()).get("mcpServers", {})
        print(f"[OK  ] .mcp.json — {len(servers)} core servers: {', '.join(servers)}")
    except Exception as e:  # noqa: BLE001
        print(f"[MISS] .mcp.json — {e}")
    if config.MCP_CATALOG.exists():
        print(f"[OK  ] catalog — {len(list(config.MCP_CATALOG.glob('*.json')))} bundles")
    print(f"[..  ] active context: {context.active()}   vault: {context.VAULT}")

    if "--ping" in sys.argv:
        try:
            from anthropic import Anthropic
            m = Anthropic().messages.create(
                model=config.MODEL_FAST, max_tokens=5,
                messages=[{"role": "user", "content": "ping"}])
            print(f"[OK  ] live model ping -> {m.model}")
        except Exception as e:  # noqa: BLE001
            print(f"[MISS] live model ping failed: {e}")

    print("\nFix MISS rows, then:  py -m jarvis.chat   (text mode, no mic needed)")


if __name__ == "__main__":
    main()
