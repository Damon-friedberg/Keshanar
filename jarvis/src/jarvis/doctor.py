"""Preflight check:  py -m jarvis.doctor

Verifies API keys, required CLIs, model config, and that the MCP files parse —
so you know exactly what's missing before the first run.
"""
import json
import os
import shutil

from . import config


def _mark(ok: bool) -> str:
    return "OK  " if ok else "MISS"


def main() -> None:
    print("JARVIS doctor\n=============")

    print(f"[{_mark(bool(os.getenv('ANTHROPIC_API_KEY')))}] env ANTHROPIC_API_KEY (required)")
    for k in ("ELEVENLABS_API_KEY", "COMPOSIO_API_KEY", "EXA_API_KEY",
              "FIRECRAWL_API_KEY", "CONTEXT7_API_KEY", "GITHUB_TOKEN"):
        flag = "ok  " if os.getenv(k) else "--  "
        print(f"[{flag}] env {k} (optional)")

    for cli in ("npx", "uvx", "claude"):
        print(f"[{_mark(bool(shutil.which(cli)))}] cli {cli}")

    print(f"[..  ] models  fast={config.MODEL_FAST}  heavy={config.MODEL_HEAVY}")

    try:
        servers = json.loads(config.MCP_CORE.read_text()).get("mcpServers", {})
        print(f"[OK  ] .mcp.json parses — {len(servers)} core servers: {', '.join(servers)}")
    except Exception as e:  # noqa: BLE001
        print(f"[MISS] .mcp.json — {e}")

    if config.MCP_CATALOG.exists():
        bundles = sorted(p.name for p in config.MCP_CATALOG.glob("*.json"))
        print(f"[OK  ] catalog — {len(bundles)} bundles: {', '.join(bundles)}")

    print("\nFill any MISS rows (.env / install Node + uv + Claude Code), then: py -m jarvis.main")


if __name__ == "__main__":
    main()
