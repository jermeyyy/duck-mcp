"""Tests for the Duck MCP Server"""
import pytest
from fastmcp import Client
from server import mcp


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
        
        assert "select_option" in tool_names
        assert "provide_information" in tool_names


@pytest.mark.asyncio
async def test_select_option_tool():
    """Test the select_option tool with user elicitation"""
    
    async def mock_elicitation_handler(message: str, response_type, params, context):
        # For list-based response_type, FastMCP generates a schema
        # with a "value" field. The handler must return {"value": selected_option}
        return {"value": "Option 1"}
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "select_option",
            {
                "question": "Which option do you prefer?",
                "options": ["Option 1", "Option 2", "Option 3"]
            }
        )
        assert "Selected: Option 1" in result.data


@pytest.mark.asyncio
async def test_select_option_other():
    """Test the select_option tool when user selects 'Other' option"""
    
    call_count = 0
    
    async def mock_elicitation_handler(message: str, response_type, params, context):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            # First elicitation: select "Other" option
            return {"value": "Other (provide answer)"}
        else:
            # Second elicitation: provide custom description
            return {"value": "My custom option description"}
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "select_option",
            {
                "question": "Which option do you prefer?",
                "options": ["Option 1", "Option 2", "Option 3"]
            }
        )
        assert "Selected: My custom option description" in result.data
        assert call_count == 2  # Verify two elicitations occurred


@pytest.mark.asyncio
async def test_provide_information_tool():
    """Test the provide_information tool with user elicitation"""
    from fastmcp.client.elicitation import ElicitResult
    
    async def mock_elicitation_handler(message: str, response_type: type, params, context):
        # Simulate user providing information
        return response_type(information="This is my answer")
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "provide_information",
            {"question": "What is your favorite color?"}
        )
        assert "User provided: This is my answer" in result.data
