# src/main.py
from mcp.server.fastmcp import FastMCP # <-- Correct import path

# --- 1. Create the FastMCP Server App ---
mcp = FastMCP(
    name="gsheets",
    title="Google Sheets MCP Server",
    description="A tool server for reading from and writing to Google Sheets."
)

# --- 2. Tool definitions will go here ---
# Example:
# @mcp.tool()
# def append_to_sheet(...) -> str:
#     """Appends a row to a Google Sheet."""
#     # ... implementation ...

# --- 3. Expose the underlying FastAPI app for Uvicorn ---
app = mcp.app

# --- Optional: Keep the root endpoint for health checks ---
@app.get("/")
def read_root():
    return {"status": "ok", "service": "gsheets_server"}