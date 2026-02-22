#!/bin/bash
set -e

echo "🦆 Testing Duck MCP Server..."

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Typecheck UI
echo "🎨 Typechecking MCP App UI..."
cd ui && npm ci && npm run typecheck && cd ..

# Run tests with coverage
echo "🧪 Running tests..."
uv run pytest tests/ -v --cov=. --cov-report=html --cov-report=term

echo "✅ Tests complete! Coverage report generated in htmlcov/"
