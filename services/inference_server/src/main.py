# src/main.py
from typing import List, Optional
from fastapi import FastAPI
from fastmcp import FastMCP

# --- Local Imports ---
from .inference import model_manager

# 1. Create a base FastAPI app.
base_app = FastAPI(title="Agentic Garden Inference Server")

# 2. Use FastMCP to CONFIGURE the base app.
# This modifies base_app in-place, adding the MCP routes to it.
mcp = FastMCP.from_fastapi(app=base_app)

# 3. Define our custom tools on the generated MCP instance.
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

# 4. Expose the original, now-modified, base_app for Uvicorn to run.
app = base_app

