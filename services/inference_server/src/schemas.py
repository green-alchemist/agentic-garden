# src/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = 512
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stream: bool = False

