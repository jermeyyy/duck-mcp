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


@pytest.mark.asyncio
async def test_ask_questions_tool_exists():
    """Verify ask_questions appears in tool listing."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "ask_questions" in tool_names


@pytest.mark.asyncio
async def test_ask_questions_returns_answers():
    """Call ask_questions, then submit_answers concurrently, verify answers are returned."""
    import asyncio

    async with Client(mcp) as client:
        expected_answers = {"q1": "A"}

        async def submit_after_delay():
            await asyncio.sleep(0.1)
            await client.call_tool(
                "submit_answers",
                {"session_id": "", "answers": expected_answers},
            )

        submit_task = asyncio.create_task(submit_after_delay())

        result = await client.call_tool(
            "ask_questions",
            {
                "questions": [
                    {
                        "id": "q1",
                        "type": "single_select",
                        "label": "Pick one",
                        "options": ["A", "B"],
                        "required": True,
                    }
                ]
            },
        )

        await submit_task

        import json
        data = json.loads(result.data)
        assert data == expected_answers


@pytest.mark.asyncio
async def test_ask_questions_has_ui_meta():
    """Verify ask_questions tool is linked to the MCP App resource via meta."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        ask_q = next(t for t in tools if t.name == "ask_questions")
        assert ask_q.meta is not None
        ui_meta = ask_q.meta.get("ui", {})
        assert ui_meta.get("resourceUri") == "ui://duck/mcp-app.html"


@pytest.mark.asyncio
async def test_submit_answers_no_pending_session():
    """Call submit_answers without a pending ask_questions, verify error."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "submit_answers",
            {"session_id": "", "answers": {"q1": "A"}},
        )
        import json
        data = json.loads(result.data)
        assert "error" in data


@pytest.mark.asyncio
async def test_mcp_app_resource_exists():
    """Verify ui://duck/mcp-app.html is in resource listing."""
    async with Client(mcp) as client:
        resources = await client.list_resources()
        resource_uris = [str(r.uri) for r in resources]
        assert "ui://duck/mcp-app.html" in resource_uris


@pytest.mark.asyncio
async def test_mcp_app_resource_serves_html():
    """Read the resource and verify it returns HTML content (requires dist/mcp-app.html to exist)."""
    from pathlib import Path

    dist_path = Path(__file__).parent.parent / "dist" / "mcp-app.html"
    if not dist_path.exists():
        pytest.skip("dist/mcp-app.html not built yet — run 'make build-ui' first")

    async with Client(mcp) as client:
        content = await client.read_resource("ui://duck/mcp-app.html")
        text = content[0].text if hasattr(content[0], "text") else str(content[0])
        assert "<!DOCTYPE html>" in text or "<html" in text
