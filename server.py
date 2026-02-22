"""
Duck MCP Server - A simple MCP server built with FastMCP
"""
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from fastmcp import FastMCP, Context
from fastmcp.server.apps import AppConfig

# Create the FastMCP server instance
mcp = FastMCP(name="Duck MCP Server")

RESOURCE_URI = "ui://duck/mcp-app.html"
UI_DIST_PATH = Path(__file__).parent / "dist" / "mcp-app.html"

_pending_event: asyncio.Event | None = None
_pending_answers: dict | None = None


@mcp.tool
async def select_option(ctx: Context, question: str, options: list[str]) -> str:
    """
    Ask user to select one option from provided choices using a single-select UI.
    
    Includes an "Other" option that allows users to provide a custom answer
    via a follow-up elicitation.
    
    Args:
        question: Detailed but brief question to ask the user
        options: List of detailed but brief options for the user to choose from
    
    Returns:
        The selected option or status message
    """
    OTHER_OPTION = "Other (provide answer)"
    
    # Add "Other" option to allow custom answers
    options_with_other = options + [OTHER_OPTION]
    
    # First elicitation: single-select from constrained options
    result = await ctx.elicit(
        message=question,
        response_type=options_with_other  # List of strings -> enum schema
    )
    
    if result.action == "accept":
        if result.data == OTHER_OPTION:
            # Second elicitation: get custom answer description
            custom_result = await ctx.elicit(
                message="Please describe your preferred option:",
                response_type=str
            )
            
            if custom_result.action == "accept":
                return f"Selected: {custom_result.data}"
            elif custom_result.action == "decline":
                return "User declined to provide custom option"
            else:  # cancel
                return "User declined to select an option"
        else:
            return f"Selected: {result.data}"
    elif result.action == "decline":
        return "User declined to select an option"
    else:  # cancel
        return "Selection cancelled by user"


@mcp.tool
async def provide_information(ctx: Context, question: str) -> str:
    """
    Request additional information from user in natural language.
    
    Args:
        question: Detailed but brief question asking for specific information
    
    Returns:
        The user's response or status message
    """
    @dataclass
    class UserResponse:
        information: str
    
    result = await ctx.elicit(
        message=question,
        response_type=UserResponse
    )
    
    if result.action == "accept":
        return f"User provided: {result.data.information}"
    elif result.action == "decline":
        return "User declined to provide information"
    else:  # cancel
        return "Information request cancelled by user"


@mcp.tool
async def request_manual_test(ctx: Context, test_description: str, expected_outcome: str = "") -> str:
    """
    Request the user to perform manual testing and report results.
    
    This tool allows an agent to ask a user to perform manual testing of functionality,
    and then collect the results via elicitation for analysis.
    
    Args:
        test_description: Detailed description of what manual testing should be performed
        expected_outcome: Optional description of what the expected outcome should be
    
    Returns:
        The test results reported by the user or status message
    """
    @dataclass
    class TestResult:
        result: str
        success: bool
    
    # Build the elicitation message
    message_parts = [f"Please perform the following manual test:\n\n{test_description}"]
    
    if expected_outcome:
        message_parts.append(f"\nExpected outcome:\n{expected_outcome}")
    
    message_parts.append("\n\nPlease report the results below:")
    elicitation_message = "".join(message_parts)
    
    result = await ctx.elicit(
        message=elicitation_message,
        response_type=TestResult
    )
    
    if result.action == "accept":
        success_indicator = "✓ PASSED" if result.data.success else "✗ FAILED"
        return f"Test Result: {success_indicator}\n\nReport:\n{result.data.result}"
    elif result.action == "decline":
        return "User declined to perform manual testing"
    else:  # cancel
        return "Manual testing request cancelled by user"


@mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI))
async def ask_questions(questions: list[dict], ctx: Context) -> str:
    """
    Ask the user one or more questions via an interactive form UI.

    Each question has: id, type (single_select | multi_select | text),
    label, options (for select types), and required (bool).

    Args:
        questions: List of question configuration objects

    Returns:
        JSON string with the user's answers
    """
    global _pending_event, _pending_answers
    _pending_event = asyncio.Event()
    _pending_answers = None

    try:
        await asyncio.wait_for(_pending_event.wait(), timeout=300)
        return json.dumps(_pending_answers)
    except asyncio.TimeoutError:
        return json.dumps({"error": "Question session timed out after 5 minutes"})
    finally:
        _pending_event = None
        _pending_answers = None


@mcp.tool(
    app=AppConfig(
        resource_uri=RESOURCE_URI,
        visibility=["app"],
    )
)
async def submit_answers(answers: dict, session_id: str = "") -> str:
    """
    Receive answers from the MCP App form UI.
    Called by the MCP App when the user submits the form.

    Args:
        answers: Dictionary mapping question IDs to user answers
        session_id: Optional session ID (kept for backward compatibility)

    Returns:
        Confirmation of received answers
    """
    global _pending_event, _pending_answers

    if _pending_event is None:
        return json.dumps({"error": "No pending question session"})

    _pending_answers = answers
    _pending_event.set()
    return json.dumps({"status": "received"})


@mcp.resource(RESOURCE_URI)
def mcp_app_resource() -> str:
    """Serve the MCP App HTML for the ask_questions tool UI."""
    if not UI_DIST_PATH.exists():
        raise FileNotFoundError(
            f"MCP App HTML not found at {UI_DIST_PATH}. "
            "Run 'make build-ui' to build the UI first."
        )
    return UI_DIST_PATH.read_text(encoding="utf-8")


if __name__ == "__main__":
    # Run the server with stdio transport by default
    mcp.run()
