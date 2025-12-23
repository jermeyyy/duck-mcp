"""
Duck MCP Server - A simple MCP server built with FastMCP
"""
import random
from dataclasses import dataclass
from fastmcp import FastMCP, Context

# Create the FastMCP server instance
mcp = FastMCP(name="Duck MCP Server")


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


if __name__ == "__main__":
    # Run the server with stdio transport by default
    mcp.run()
