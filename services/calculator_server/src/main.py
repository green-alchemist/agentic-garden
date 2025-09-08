# src/main.py
from fastapi import FastAPI
from fastmcp import FastMCP

# 1. Create a standard FastAPI app. This will be our runnable app.
app = FastAPI(title="Agentic Garden Calculator Server")

# 2. Define our tools as standard FastAPI routes, following the MCP path convention.
@app.post("/tools/add")
def add(a: float, b: float) -> float:
    """Adds two numbers together."""
    return a + b

@app.post("/tools/subtract")
def subtract(a: float, b: float) -> float:
    """Subtracts the second number from the first."""
    return a - b

# 3. Use FastMCP to ensure the app's schema is MCP-compliant.
# This modifies 'app' in-place and makes it discoverable.
mcp = FastMCP.from_fastapi(app=app)

