#!/usr/bin/env bash
# Register Jarvis's MCP core into Claude Code (user scope). macOS / Linux / WSL.
# Export the API keys (or source your .env) before running.
set +e
echo "Adding Jarvis MCP core to Claude Code (user scope)..."

claude mcp add --scope user desktop-commander  -- npx -y @wonderwhy-er/desktop-commander
claude mcp add --scope user terminator         -- npx -y terminator-mcp-agent@latest
claude mcp add --scope user playwright         -- npx -y @playwright/mcp@latest
claude mcp add --scope user serena             -- uvx --from git+https://github.com/oraios/serena serena-mcp-server --context ide-assistant
claude mcp add --scope user sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
claude mcp add --scope user basic-memory       -- uvx basic-memory mcp
claude mcp add --scope user screenpipe         -- npx -y screenpipe-mcp@latest
claude mcp add --scope user composio  -e COMPOSIO_API_KEY="$COMPOSIO_API_KEY"   -- npx -y @composio/mcp@latest
claude mcp add --scope user firecrawl -e FIRECRAWL_API_KEY="$FIRECRAWL_API_KEY" -- npx -y firecrawl-mcp

claude mcp add --scope user --transport http exa      "https://mcp.exa.ai/mcp"             --header "x-api-key: $EXA_API_KEY"
claude mcp add --scope user --transport http context7 "https://mcp.context7.com/mcp"       --header "CONTEXT7_API_KEY: $CONTEXT7_API_KEY"
claude mcp add --scope user --transport http github   "https://api.githubcopilot.com/mcp/" --header "Authorization: Bearer $GITHUB_TOKEN"

echo "Done. Run 'claude mcp list' to verify."
