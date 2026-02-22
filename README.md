# Duck MCP Server 🦆

A simple MCP (Model Context Protocol) server built with [FastMCP](https://gofastmcp.com/).

## Features

This server provides the following tools:

### Elicitation Tools
- **select_option**: Ask user to select one option from provided choices (uses elicitation)
- **provide_information**: Request additional information from user in natural language (uses elicitation)
- **request_manual_test**: Request the user to perform manual testing and report results (uses elicitation)

### MCP Apps
- **ask_questions**: Ask the user one or more questions via an interactive form UI rendered in a sandboxed iframe. Supports single-select (radio buttons), multi-select (checkboxes), and free-text question types in a pager/wizard layout.

The `ask_questions` tool uses the [MCP Apps extension](https://modelcontextprotocol.io/docs/extensions/apps) to render a React-based form UI directly inside MCP hosts that support it (Claude Desktop, VS Code Copilot, etc.). For hosts that don't support Apps, the questions are returned as plain text.

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip
- Node.js 18+ and npm (for building the MCP App UI)

### Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -e .
```

### Build the MCP App UI

The `ask_questions` tool requires the React UI to be built:

```bash
make build-ui
```

Or manually:
```bash
cd ui && npm ci && npm run build
```

This produces `dist/mcp-app.html`, a single HTML file with all JS/CSS inlined.

## Usage

### Running the Server

#### Using the FastMCP CLI (recommended):
```bash
# Run with default configuration from fastmcp.json
fastmcp run

# Or specify the config file explicitly
fastmcp run fastmcp.json

# Run with HTTP transport for testing
fastmcp run --transport http --port 8000
```

#### Using Python directly:
```bash
python server.py
```

### Running with uv:
```bash
uv run fastmcp run server.py
```

### Development Mode

Run with the FastMCP Inspector UI:
```bash
fastmcp dev
```

### Inspect Server Capabilities

View all available tools, resources, and prompts:
```bash
fastmcp inspect
```

## Installing to MCP Clients

### Claude Desktop

```bash
fastmcp install claude-desktop
```

### Cursor

```bash
fastmcp install cursor
```

### Claude Code (VS Code Extension)

```bash
fastmcp install claude-code
```

## Testing

Run all tests:
```bash
make test
```

Run with coverage:
```bash
make test-coverage
```

Typecheck the UI:
```bash
make test-ui
```

## Project Structure

```
duck-mcp/
├── server.py          # Main server implementation
├── fastmcp.json       # FastMCP configuration
├── pyproject.toml     # Project metadata and dependencies
├── Makefile           # Build, test, and development targets
├── README.md          # This file
├── tests/             # Python tests
│   └── test_server.py
├── scripts/           # Build and deployment scripts
│   ├── build.sh
│   ├── deploy.sh
│   └── test.sh
├── ui/                # React MCP App source (pager/wizard form UI)
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── mcp-app.html   # Vite entry HTML
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── types.ts
│       ├── components/
│       │   ├── QuestionPager.tsx
│       │   ├── PagerControls.tsx
│       │   ├── SingleSelectPage.tsx
│       │   ├── MultiSelectPage.tsx
│       │   ├── TextInputPage.tsx
│       │   └── Markdown.tsx
│       └── styles/
│           └── app.css
└── dist/              # Built UI output (gitignored)
    └── mcp-app.html
```

## Development

### Adding New Tools

To add a new tool to the server, simply decorate a function with `@mcp.tool`:

```python
@mcp.tool
def my_new_tool(arg1: str, arg2: int) -> str:
    """Description of what this tool does"""
    return "result"
```

### Running Tests

```bash
make test
```

### Building

```bash
make build  # Builds UI + Python package
```

## MCP Apps Compatibility

The `ask_questions` tool requires an MCP host that supports the [MCP Apps extension](https://modelcontextprotocol.io/docs/extensions/apps) (`io.modelcontextprotocol/ui`). Known compatible hosts:
- Claude Desktop
- VS Code Copilot (Insiders)

For hosts without Apps support, the tool returns the questions as plain text for the agent to work with.

## Configuration

The `fastmcp.json` file contains the server configuration:

- **source**: Location and entrypoint of the server code
- **environment**: Python version and dependencies
- **deployment**: Runtime configuration (transport, logging, etc.)

### MCP Client Configuration

To use this MCP server with MCP-compatible clients, add the following configuration:

#### Using uv (recommended):
```json
{
  "mcpServers": {
    "duck-mcp": {
      "command": "uv",
      "args": ["run", "fastmcp", "run", "server.py"],
      "cwd": "/path/to/duck-mcp"
    }
  }
}
```

Replace `/path/to/duck-mcp` with the actual path to your duck-mcp directory.

## Learn More

- [FastMCP Documentation](https://gofastmcp.com/)
- [MCP Apps Extension](https://modelcontextprotocol.io/docs/extensions/apps)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## License

MIT
