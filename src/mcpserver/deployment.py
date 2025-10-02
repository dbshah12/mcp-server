from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")

@mcp.tool()
def greeting(name:str) -> str:
    """Send Greetings"""
    return f"Hello, {name}!"