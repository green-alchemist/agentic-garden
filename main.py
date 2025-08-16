# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse # Import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Generator
from inference import model_manager
import os

# Define the request body for our chat endpoint using Pydantic
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    # This is the crucial part. The field must be 'messages'.
    messages: List[ChatMessage]
    
    # Optional parameters
    max_tokens: int = 512
    temperature: Optional[float] = None
    top_p: Optional[float] = None

def format_sse(data: str) -> str:
    """Formats a string as a Server-Sent Event."""
    return f"data: {data}\n\n"

# Create the FastAPI app
app = FastAPI(
    title="Agentic AI Inference Server",
    description="An API server for running local LLMs with llama-cpp-python and NVIDIA GPUs."
)

@app.on_event("startup")
def load_model():
    """Pre-load the model on server startup."""
    # The model_manager is a singleton, so this just ensures the instance is created.
    if model_manager.llm is None:
        raise RuntimeError("Model could not be loaded on startup.")
    print("🚀 Server is ready and model is loaded!")

@app.get("/")
def read_root():
    """A simple health check endpoint."""
    model_name = os.getenv("MODEL_NAME", "default")
    return {"status": "ok", f"model_loaded": model_name}

@app.post("/v1/chat/completions")
def chat_completions(request: ChatRequest):
    """An OpenAI-compatible endpoint for chat completions."""
    try:
        generation_kwargs = request.dict(exclude={"messages"}, exclude_none=True)
        
        # For now, we'll assume streaming. A more robust solution
        # would check a `stream` flag in the request.
        
        def stream_generator() -> Generator[str, None, None]:
            # The generator that yields formatted SSE data
            stream = model_manager.generate_chat_completion_stream(
                messages=[msg.dict() for msg in request.messages],
                **generation_kwargs
            )
            for chunk in stream:
                # Here you could format it to be OpenAI compatible
                # For simplicity, we just send the text
                yield format_sse(chunk)
        
        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))