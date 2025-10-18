#!/bin/bash
# Playwright MCP wrapper to unset display scaling
unset GDK_SCALE
unset GDK_DPI_SCALE
export GDK_SCALE=1
export GDK_DPI_SCALE=1
exec npx -y @playwright/mcp@latest --config /home/kdresdell/Documents/DEV/minipass_env/app/playwright-mcp-config.json "$@"
