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
        assert "request_manual_test" in tool_names


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
async def test_select_option_decline():
    """Test the select_option tool when user declines to select"""
    from fastmcp.client.elicitation import ElicitResult
    
    async def mock_elicitation_handler(message: str, response_type, params, context):
        # User declines to select an option at first elicitation
        return ElicitResult(action="decline")
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "select_option",
            {
                "question": "Which option do you prefer?",
                "options": ["Option 1", "Option 2", "Option 3"]
            }
        )
        assert "User declined to select an option" in result.data


@pytest.mark.asyncio
async def test_select_option_cancel():
    """Test the select_option tool when user cancels selection"""
    from fastmcp.client.elicitation import ElicitResult
    
    async def mock_elicitation_handler(message: str, response_type, params, context):
        # User cancels at first elicitation
        return ElicitResult(action="cancel")
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "select_option",
            {
                "question": "Which option do you prefer?",
                "options": ["Option 1", "Option 2", "Option 3"]
            }
        )
        assert "Selection cancelled by user" in result.data


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
async def test_select_option_other_decline():
    """Test the select_option tool when user declines to provide custom description"""
    from fastmcp.client.elicitation import ElicitResult
    
    call_count = 0
    
    async def mock_elicitation_handler(message: str, response_type, params, context):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            # First elicitation: select "Other" option
            return {"value": "Other (provide answer)"}
        else:
            # Second elicitation: decline to provide custom description
            return ElicitResult(action="decline")
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "select_option",
            {
                "question": "Which option do you prefer?",
                "options": ["Option 1", "Option 2", "Option 3"]
            }
        )
        assert "User declined to provide custom option" in result.data
        assert call_count == 2  # Verify two elicitations occurred


@pytest.mark.asyncio
async def test_select_option_other_cancel():
    """Test the select_option tool when user cancels custom description elicitation"""
    from fastmcp.client.elicitation import ElicitResult
    
    call_count = 0
    
    async def mock_elicitation_handler(message: str, response_type, params, context):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            # First elicitation: select "Other" option
            return {"value": "Other (provide answer)"}
        else:
            # Second elicitation: cancel the custom description
            return ElicitResult(action="cancel")
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "select_option",
            {
                "question": "Which option do you prefer?",
                "options": ["Option 1", "Option 2", "Option 3"]
            }
        )
        assert "User declined to select an option" in result.data
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


@pytest.mark.asyncio
async def test_provide_information_decline():
    """Test the provide_information tool when user declines"""
    from fastmcp.client.elicitation import ElicitResult
    
    async def mock_elicitation_handler(message: str, response_type: type, params, context):
        # Simulate user declining to provide information
        return ElicitResult(action="decline")
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "provide_information",
            {"question": "What is your favorite color?"}
        )
        assert "User declined to provide information" in result.data


@pytest.mark.asyncio
async def test_provide_information_cancel():
    """Test the provide_information tool when user cancels"""
    from fastmcp.client.elicitation import ElicitResult
    
    async def mock_elicitation_handler(message: str, response_type: type, params, context):
        # Simulate user cancelling the information request
        return ElicitResult(action="cancel")
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "provide_information",
            {"question": "What is your favorite color?"}
        )
        assert "Information request cancelled by user" in result.data


@pytest.mark.asyncio
async def test_request_manual_test_tool():
    """Test the request_manual_test tool with user elicitation"""
    from fastmcp.client.elicitation import ElicitResult
    
    async def mock_elicitation_handler(message: str, response_type: type, params, context):
        # Simulate user providing test results
        return response_type(result="Feature works as expected", success=True)
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "request_manual_test",
            {
                "test_description": "Click the submit button and verify the form submits",
                "expected_outcome": "Form should submit successfully"
            }
        )
        assert "✓ PASSED" in result.data
        assert "Feature works as expected" in result.data


@pytest.mark.asyncio
async def test_request_manual_test_tool_failed():
    """Test the request_manual_test tool when test fails"""
    from fastmcp.client.elicitation import ElicitResult
    
    async def mock_elicitation_handler(message: str, response_type: type, params, context):
        # Simulate user reporting a failed test
        return response_type(result="Button did not respond to click", success=False)
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "request_manual_test",
            {
                "test_description": "Click the submit button and verify the form submits"
            }
        )
        assert "✗ FAILED" in result.data
        assert "Button did not respond to click" in result.data


@pytest.mark.asyncio
async def test_request_manual_test_decline():
    """Test the request_manual_test tool when user declines"""
    from fastmcp.client.elicitation import ElicitResult
    
    async def mock_elicitation_handler(message: str, response_type: type, params, context):
        # Simulate user declining to perform manual test
        return ElicitResult(action="decline")
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "request_manual_test",
            {"test_description": "Click the submit button and verify the form submits"}
        )
        assert "User declined to perform manual testing" in result.data


@pytest.mark.asyncio
async def test_request_manual_test_cancel():
    """Test the request_manual_test tool when user cancels"""
    from fastmcp.client.elicitation import ElicitResult
    
    async def mock_elicitation_handler(message: str, response_type: type, params, context):
        # Simulate user cancelling the manual test request
        return ElicitResult(action="cancel")
    
    async with Client(mcp, elicitation_handler=mock_elicitation_handler) as client:
        result = await client.call_tool(
            "request_manual_test",
            {"test_description": "Click the submit button and verify the form submits"}
        )
        assert "Manual testing request cancelled by user" in result.data
