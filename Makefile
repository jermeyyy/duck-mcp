.PHONY: help install dev run test clean inspect build deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	uv sync

dev: ## Run server in development mode with inspector
	uv run fastmcp dev

run: ## Run server with stdio transport
	uv run fastmcp run

run-http: ## Run server with HTTP transport on port 8000
	uv run fastmcp run --transport http --port 8000

test: ## Run tests
	uv run pytest tests/ -v

test-coverage: ## Run tests with coverage report
	uv run pytest tests/ -v --cov=. --cov-report=html --cov-report=term

inspect: ## Inspect server capabilities
	uv run fastmcp inspect

clean: ## Clean up build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	uv build

install-claude: ## Install to Claude Desktop
	uv run fastmcp install claude-desktop

install-cursor: ## Install to Cursor
	uv run fastmcp install cursor

install-claude-code: ## Install to Claude Code (VS Code)
	uv run fastmcp install claude-code

lint: ## Run linting (if configured)
	@echo "Linting not configured yet. Add ruff or pylint to dev dependencies."

format: ## Format code (if configured)
	@echo "Formatting not configured yet. Add black or ruff to dev dependencies."
