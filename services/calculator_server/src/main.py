# src/main.py
from mcp.server.fastmcp import FastMCP

# --- 1. Create the FastMCP Server App ---
mcp = FastMCP(
    name="calculator",
    title="Calculator MCP Server",
    description="A tool server for basic arithmetic operations."
)

# --- 2. Tool Definitions ---
@mcp.tool()
def add(a: float, b: float) -> float:
    """Adds two numbers together."""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtracts the second number from the first."""
    return a - b

# --- 3. Expose the underlying FastAPI app for Uvicorn ---
app = mcp.app

# --- Optional: Keep the root endpoint for health checks ---
@app.get("/")
def read_root():
    return {"status": "ok", "service": "calculator_server"}