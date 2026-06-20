# Register Jarvis's MCP core into Claude Code at USER scope, so every Claude Code
# session (in any folder) has the same tools. Fill .env / set the env vars first.
#
#   Usage:  .\scripts\setup_claude_code.ps1
#   Verify: claude mcp list
#
# For the FULL catalog (creative / dev / research / comms / power-re / media),
# add the gateway as a single entry instead of 50 servers — see config/GATEWAY.md.

$ErrorActionPreference = "Continue"
Write-Host "Adding Jarvis MCP core to Claude Code (user scope)..."

# --- stdio servers ---
claude mcp add --scope user desktop-commander  -- npx -y "@wonderwhy-er/desktop-commander"
claude mcp add --scope user terminator         -- npx -y "terminator-mcp-agent@latest"
claude mcp add --scope user playwright          -- npx -y "@playwright/mcp@latest"
claude mcp add --scope user serena             -- uvx --from "git+https://github.com/oraios/serena" serena-mcp-server --context ide-assistant
claude mcp add --scope user sequential-thinking -- npx -y "@modelcontextprotocol/server-sequential-thinking"
claude mcp add --scope user basic-memory       -- uvx basic-memory mcp
claude mcp add --scope user screenpipe         -- npx -y "screenpipe-mcp@latest"
claude mcp add --scope user composio  -e "COMPOSIO_API_KEY=$env:COMPOSIO_API_KEY"   -- npx -y "@composio/mcp@latest"
claude mcp add --scope user firecrawl -e "FIRECRAWL_API_KEY=$env:FIRECRAWL_API_KEY" -- npx -y firecrawl-mcp

# --- http servers ---
claude mcp add --scope user --transport http exa      "https://mcp.exa.ai/mcp"            --header "x-api-key: $env:EXA_API_KEY"
claude mcp add --scope user --transport http context7 "https://mcp.context7.com/mcp"      --header "CONTEXT7_API_KEY: $env:CONTEXT7_API_KEY"
claude mcp add --scope user --transport http github   "https://api.githubcopilot.com/mcp/" --header "Authorization: Bearer $env:GITHUB_TOKEN"

Write-Host ""
Write-Host "Done. Run 'claude mcp list' to verify."
Write-Host "Note: graphiti is omitted here (needs Neo4j); basic-memory is its lightweight stand-in."
