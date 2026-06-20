# The gateway — how Jarvis gets "all the MCPs" without going dumb

**Problem:** past ~5–7 *action-heavy* servers, an agent's tool-selection accuracy
drops measurably. Wiring 50+ servers directly makes Jarvis slower and worse.

**Solution:** a two-layer setup.

```
ALWAYS-ON CORE  (.mcp.json)         ON-DEMAND CATALOG  (config/mcp_catalog/*.json)
~12 lean, high-value servers   +    creative_3d · dev_cloud · research · comms
                                     power_re · media · force_multiplier · finance(gated)
            \                              /
             \                            /
              ▼                          ▼
                 MCP GATEWAY  (one of:)
                 · MetaMCP            (Docker, namespaces + per-tool filtering)
                 · Docker MCP Toolkit (300+ catalog, container isolation)
                 · ToolHive           (per-server isolation, secrets, audit)
                          │
                 dynamic tool discovery → only the relevant ~dozen tools
                 are exposed to Claude per task
```

The gateway holds the whole catalog (plus **Composio** ≈ 20k actions and
**Smithery** ≈ 7k servers) but surfaces only what the current task needs. That's
how you get effectively unlimited capability while the live agent stays sharp.

## Quick start (MetaMCP)

```bash
git clone https://github.com/metatool-ai/metamcp && cd metamcp
cp example.env .env && docker compose up -d        # UI on http://localhost:12008
```

Then in the MetaMCP UI:
1. Create a **namespace** per bundle (e.g. `creative`, `dev`, `comms`).
2. Add the servers from the matching `config/mcp_catalog/*.json` file.
3. Enable **tool filtering** so each namespace exposes only its key tools.
4. Point Jarvis (`agent.py` → `mcp_servers`) at the single MetaMCP endpoint
   instead of the raw core, or run core direct + gateway for the long tail.

## Alternative (Docker MCP Toolkit)

```bash
# Docker Desktop 4.40+  → enable MCP Toolkit, then:
docker mcp client connect claude-code
```
Browse the 300+ verified catalog at hub.docker.com/mcp; each server runs in its
own container.

## Adding even more

Anything from your master list that isn't in a bundle: find it in the
**official registry** (registry.modelcontextprotocol.io) or **Smithery**, then
`npx -y @smithery/cli install <server> --client claude` — or add it to the right
bundle file and let the gateway pick it up. Verify a server before trusting it
(a lot of the long-tail list is unverified).
