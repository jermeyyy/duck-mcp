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
    Ask user to select one option from provided choices.
    
    Args:
        question: Detailed but brief question to ask the user
        options: List of detailed but brief options for the user to choose from
    
    Returns:
        The selected option or status message
    """
    @dataclass
    class OptionSelection:
        selected_option: str
    
    # Format options for display
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    elicitation_message = f"{question}\n\nOptions:\n{options_text}\n\nPlease select an option by entering its number or text:"
    
    result = await ctx.elicit(
        message=elicitation_message,
        response_type=OptionSelection
    )
    
    if result.action == "accept":
        return f"Selected: {result.data.selected_option}"
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


if __name__ == "__main__":
    # Run the server with stdio transport by default
    mcp.run()
