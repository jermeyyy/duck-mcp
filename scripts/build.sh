#!/bin/bash
set -e

echo "🦆 Building Duck MCP Server..."

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Run tests
echo "🧪 Running tests..."
uv run pytest tests/ -v

# Build package
echo "📦 Building package..."
uv build

echo "✅ Build complete!"
