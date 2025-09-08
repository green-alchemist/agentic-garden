# src/main.py
from fastapi import FastAPI
from fastmcp import FastMCP

# 1. Create a base FastAPI app.
# We won't add routes to it directly, but it's needed for the constructor.
base_app = FastAPI(title="Agentic Garden Calculator Server")

# 2. Create the MCP server FROM the base app.
# This uses the documented factory method to create a runnable server instance.
mcp = FastMCP.from_fastapi(app=base_app)

# 3. Define our custom tools on the generated MCP instance.
@mcp.tool()
def add(a: float, b: float) -> float:
    """Adds two numbers together."""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtracts the second number from the first."""
    return a - b

# 4. Expose the runnable mcp object for Uvicorn.
# We name it 'app' so our 'uvicorn main:app' command still works.
app = base_app

