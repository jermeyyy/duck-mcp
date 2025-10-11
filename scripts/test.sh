#!/bin/bash
set -e

echo "🦆 Testing Duck MCP Server..."

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Run tests with coverage
echo "🧪 Running tests..."
uv run pytest tests/ -v --cov=. --cov-report=html --cov-report=term

echo "✅ Tests complete! Coverage report generated in htmlcov/"
