# src/main.py
from typing import List, Optional
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# --- Local Imports ---
from .inference import model_manager

# --- 1. Create the FastMCP instance to define tools ---
mcp = FastMCP("inference")

# --- 2. Define the Chat Completion Tool on the MCP instance ---
@mcp.tool()
def create_chat_completion(
    messages: List[dict],
    temperature: Optional[float] = 0.1,
    stream: Optional[bool] = False
) -> dict:
    """Generates a chat completion response from the loaded LLM."""
    generation_kwargs = {"temperature": temperature}
    response_text = model_manager.generate_chat_completion(
        messages=messages, **generation_kwargs
    )
    return {"choices": [{"message": {"role": "assistant", "content": response_text.strip()}}]}

# --- 3. Create a standard FastAPI app and mount the MCP server ---
# This is the robust, standard way to serve a sub-application.
app = FastAPI(title="Agentic Garden MCP Gateway")
app.mount("/mcp", mcp)

# --- 4. Optional: Add a root health check to the main app ---
@app.get("/")
def read_root():
    return {"status": "ok", "service": "inference_server"}