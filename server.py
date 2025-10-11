"""
Duck MCP Server - A simple MCP server built with FastMCP
"""
import random
from fastmcp import FastMCP

# Create the FastMCP server instance
mcp = FastMCP(name="Duck MCP Server")


@mcp.tool
def greet(name: str) -> str:
    """Greet a user by name"""
    return f"🦆 Hello, {name}! Welcome to Duck MCP Server!"


@mcp.tool
def roll_dice(n_dice: int = 1) -> list[int]:
    """Roll n_dice 6-sided dice and return the results"""
    if n_dice < 1 or n_dice > 10:
        raise ValueError("Number of dice must be between 1 and 10")
    return [random.randint(1, 6) for _ in range(n_dice)]


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b


if __name__ == "__main__":
    # Run the server with stdio transport by default
    mcp.run()
