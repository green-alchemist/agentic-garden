# src/agents/coding_assistant.py
import os
import requests
import json
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END

# This is the single, correct state for our graph.
# It defines all the data that can be passed between nodes.
class AgentState(TypedDict):
    messages: List[dict]
    temperature: Optional[float]
    generation: str

def call_model(state: AgentState):
    """Calls the inference server for a single, non-streaming response."""
    url = os.getenv("INFERENCE_API_URL", "http://inference-engine:8000/v1/chat/completions")
    
    # Prepare the payload by extracting relevant keys from the state
    payload = {
        "messages": state['messages'],
        "temperature": state.get('temperature', 0.1), # Default to 0.1 if not provided
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        generation = data['choices'][0]['message']['content']
        # The node only needs to return the part of the state it changed
        return {"generation": generation}

    except requests.exceptions.RequestException as e:
        return {"generation": f"\n[ERROR] API call failed: {e}\n"}

# The StateGraph must be initialized with the complete AgentState
workflow = StateGraph(AgentState)
workflow.add_node("llm", call_model)
workflow.set_entry_point("llm")
workflow.add_edge("llm", END)
agent_app = workflow.compile()