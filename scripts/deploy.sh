#!/bin/bash
set -e

echo "🦆 Deploying Duck MCP Server..."

# Check if deployment target is specified
if [ -z "$1" ]; then
    echo "Usage: ./scripts/deploy.sh [claude-desktop|cursor|claude-code|http]"
    exit 1
fi

TARGET=$1

case $TARGET in
    claude-desktop)
        echo "📦 Installing to Claude Desktop..."
        uv run fastmcp install claude-desktop
        echo "✅ Installed to Claude Desktop. Restart Claude Desktop to use the server."
        ;;
    cursor)
        echo "📦 Installing to Cursor..."
        uv run fastmcp install cursor
        echo "✅ Installed to Cursor. Restart Cursor to use the server."
        ;;
    claude-code)
        echo "📦 Installing to Claude Code (VS Code)..."
        uv run fastmcp install claude-code
        echo "✅ Installed to Claude Code. Restart VS Code to use the server."
        ;;
    http)
        echo "🚀 Starting HTTP server..."
        PORT=${2:-8000}
        echo "Server will be available at http://localhost:$PORT/mcp"
        uv run fastmcp run --transport http --host 0.0.0.0 --port $PORT
        ;;
    *)
        echo "❌ Unknown deployment target: $TARGET"
        echo "Available targets: claude-desktop, cursor, claude-code, http"
        exit 1
        ;;
esac
