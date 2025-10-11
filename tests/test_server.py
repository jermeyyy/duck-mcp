"""Tests for the Duck MCP Server"""
import pytest
from fastmcp import Client
from server import mcp


@pytest.mark.asyncio
async def test_greet_tool():
    """Test the greet tool"""
    async with Client(mcp) as client:
        result = await client.call_tool("greet", {"name": "Test User"})
        assert "Test User" in result.data
        assert "🦆" in result.data


@pytest.mark.asyncio
async def test_roll_dice_tool():
    """Test the roll_dice tool"""
    async with Client(mcp) as client:
        # Test default (1 die)
        result = await client.call_tool("roll_dice", {})
        assert isinstance(result.data, list)
        assert len(result.data) == 1
        assert 1 <= result.data[0] <= 6
        
        # Test multiple dice
        result = await client.call_tool("roll_dice", {"n_dice": 3})
        assert len(result.data) == 3
        for value in result.data:
            assert 1 <= value <= 6


@pytest.mark.asyncio
async def test_roll_dice_validation():
    """Test dice rolling validation"""
    async with Client(mcp) as client:
        # Test invalid number of dice (too few)
        with pytest.raises(Exception):
            await client.call_tool("roll_dice", {"n_dice": 0})
        
        # Test invalid number of dice (too many)
        with pytest.raises(Exception):
            await client.call_tool("roll_dice", {"n_dice": 11})


@pytest.mark.asyncio
async def test_add_tool():
    """Test the add tool"""
    async with Client(mcp) as client:
        result = await client.call_tool("add", {"a": 5, "b": 3})
        assert result.data == 8
        
        result = await client.call_tool("add", {"a": -10, "b": 15})
        assert result.data == 5


@pytest.mark.asyncio
async def test_server_ping():
    """Test server connectivity"""
    async with Client(mcp) as client:
        assert await client.ping()


@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available tools"""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        
        assert "greet" in tool_names
        assert "roll_dice" in tool_names
        assert "add" in tool_names
