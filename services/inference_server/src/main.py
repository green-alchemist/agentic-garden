# src/main.py
from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel
from fastmcp import FastMCP

# --- Local Imports ---
from .inference import model_manager

# 1. Create a standard FastAPI app. This will be our runnable app.
app = FastAPI(title="Agentic Garden Inference Server")

# 2. Define a Pydantic model for the request body. This is a robust way to define an API contract.
class ChatCompletionRequest(BaseModel):
    messages: List[Dict[str, Any]]
    temperature: Optional[float] = 0.1
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = "auto"

# 3. Define our tool as a standard FastAPI route, accepting the Pydantic model.
@app.post("/tools/create_chat_completion")
def create_chat_completion(request: ChatCompletionRequest) -> dict:
    """Generates a chat completion response from the loaded LLM."""
    generation_kwargs = {
        "temperature": request.temperature,
        "tools": request.tools,
        "tool_choice": request.tool_choice
    }
    
    # Filter out None values before passing to the model manager
    generation_kwargs = {k: v for k, v in generation_kwargs.items() if v is not None}

    response_data = model_manager.generate_chat_completion(
        messages=request.messages, **generation_kwargs
    )
    
    # THE FIX: The model manager now always returns the full message dictionary.
    # We can pass it directly into the response.
    return {"choices": [{"message": response_data}]}

# 4. Use FastMCP to ensure the app's schema is MCP-compliant.
mcp = FastMCP.from_fastapi(app=app)

