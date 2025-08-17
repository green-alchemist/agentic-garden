# src/main.py
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

# --- Local Imports ---
from .inference import model_manager
from .schemas import ChatRequest

# --- FastAPI Application Setup ---
app = FastAPI(
    title="Agentic AI Inference Server",
    description="An API server for running local LLMs."
)

@app.on_event("startup")
def load_model():
    if model_manager.llm is None:
        raise RuntimeError("Model could not be loaded on startup.")
    print("🚀 Server is ready and model is loaded!")

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "ok", "model_loaded": model_manager.model_name or "Unknown"}

@app.post("/v1/chat/completions")
def chat_completions(request: ChatRequest):
    """Handles both streaming and non-streaming chat completions."""
    generation_kwargs = request.dict(exclude={"messages", "stream"}, exclude_none=True)
    messages = [msg.dict() for msg in request.messages]

    try:
        if request.stream:
            # ** THE FIX IS HERE **
            # We must create a new generator that ITERATES over the model_manager's
            # generator to properly stream the response.
            def response_generator():
                for chunk in model_manager.generate_chat_completion_stream(
                    messages=messages, **generation_kwargs
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            return StreamingResponse(response_generator(), media_type="text/event-stream")
        else:
            response_text = model_manager.generate_chat_completion(
                messages=messages, **generation_kwargs
            )
            return JSONResponse(
                content={"choices": [{"message": {"role": "assistant", "content": response_text.strip()}}]}
            )
            
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))