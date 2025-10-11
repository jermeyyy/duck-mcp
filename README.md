# Duck MCP Server 🦆

A simple MCP (Model Context Protocol) server built with [FastMCP](https://gofastmcp.com/).

## Features

This server provides the following tools:
- **greet**: Greet a user by name
- **roll_dice**: Roll 1-10 six-sided dice
- **add**: Add two numbers together

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip

### Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -e .
```

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

You can test the server using a FastMCP client:

```python
import asyncio
from fastmcp import Client

async def test_server():
    async with Client("http://localhost:8000/mcp") as client:
        # Test the greet tool
        result = await client.call_tool("greet", {"name": "World"})
        print(result.data)
        
        # Test the roll_dice tool
        result = await client.call_tool("roll_dice", {"n_dice": 3})
        print(result.data)

if __name__ == "__main__":
    asyncio.run(test_server())
```

## Project Structure

```
duck-mcp/
├── server.py          # Main server implementation
├── fastmcp.json       # FastMCP configuration
├── pyproject.toml     # Project metadata and dependencies
├── README.md          # This file
└── tests/            # Test files (optional)
```

## Development

### Adding New Tools

To add a new tool to the server, simply decorate a function with `@mcp.tool`:

```python
@mcp.tool
def my_new_tool(arg1: str, arg2: int) -> str:
    """Description of what this tool does"""
    # Your implementation here
    return "result"
```

### Running Tests

```bash
pytest
```

## Deployment

### Local Deployment

The server runs with stdio transport by default, making it compatible with local MCP clients like Claude Desktop.

### HTTP Deployment

For remote access, run with HTTP transport:

```bash
fastmcp run --transport http --host 0.0.0.0 --port 8000
```

### FastMCP Cloud

Deploy to FastMCP Cloud for managed hosting (requires account):

```bash
fastmcp cloud deploy
```

## Configuration

The `fastmcp.json` file contains the server configuration:

- **source**: Location and entrypoint of the server code
- **environment**: Python version and dependencies
- **deployment**: Runtime configuration (transport, logging, etc.)

You can override any configuration via CLI arguments:

```bash
fastmcp run --port 8080 --log-level DEBUG
```

## Learn More

- [FastMCP Documentation](https://gofastmcp.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)

## License

MIT
