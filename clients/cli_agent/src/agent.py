# clients/cli_agent/src/agent.py
import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from .mcp_client import MCPClient

# --- Connect to our MCP servers ---
inference_client = MCPClient(server_url="http://inference_server:8000/mcp")
calculator_client = MCPClient(server_url="http://calculator_server:8000/mcp")


# --- Define the Agent's State ---
class AgentState(TypedDict):
    messages: List[BaseMessage]

# --- Define the Agent's Nodes (Actions) ---
def call_inference_model(state: AgentState):
    """The 'brain' of the agent. Decides what to do next."""
    print("🧠 Thinking...")
    
    messages_for_api = [{"role": msg.type, "content": msg.content} for msg in state['messages']]
    
    response = inference_client.call_tool(
        "create_chat_completion",
        messages=messages_for_api,
        temperature=0.1
    )
    
    ai_message_content = "Error: Could not parse response from model."
    if isinstance(response, dict):
        ai_message_content = response.get("choices", [{}])[0].get("message", {}).get("content", ai_message_content)

    ai_message = AIMessage(content=ai_message_content)
    
    return {"messages": state['messages'] + [ai_message]}

# --- Build the Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("llm", call_inference_model)
workflow.set_entry_point("llm")
workflow.add_edge("llm", END)
agent_app = workflow.compile()