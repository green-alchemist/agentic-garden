# clients/cli_agent/src/agent.py
import os
import json
import uuid
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
# THE FIX: ToolMessage is no longer needed
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from .mcp_client import MCPClient

# --- Connect to our MCP servers ---
inference_client = MCPClient(server_url="http://inference_server:8000")
calculator_client = MCPClient(server_url="http://calculator_server:8000")

# --- Define the Agent's State ---
class AgentState(TypedDict):
    messages: List[BaseMessage]

# --- Define the Tools for the LLM ---
# This is the JSON schema the model will see.
tools = [
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "Adds two numbers together.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "subtract",
            "description": "Subtracts the second number from the first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"],
            },
        },
    }
]

# --- Helper function for role mapping ---
def map_message_to_api(message: BaseMessage) -> Dict[str, Any]:
    """Maps a LangChain message to the format expected by the LLM API."""
    role_map = {
        "human": "user",
        "ai": "assistant",
        # "tool" role is no longer used
    }
    role = role_map.get(message.type, "user")
    
    # Handle AIMessage with tool_calls specifically
    if isinstance(message, AIMessage) and message.tool_calls:
        return {
            "role": role, 
            "content": message.content or "",
            "tool_calls": message.tool_calls
        }
    
    # Default for HumanMessage, standard AIMessage, and our new tool result message
    return {"role": role, "content": message.content}


# --- Define the Agent's Nodes (Actions) ---

def call_inference_model(state: AgentState):
    """The 'brain' of the agent. Decides what to do next."""
    print("🧠 Thinking...")
    
    messages_for_api = [map_message_to_api(msg) for msg in state['messages']]
    
    response = inference_client.call_tool(
        "create_chat_completion",
        messages=messages_for_api,
        temperature=0,
        tools=tools,
        tool_choice="auto"
    )
    
    if isinstance(response, str):
        print(f"Error from server: {response}")
        ai_message = AIMessage(content="I'm sorry, I encountered an error. Please check the logs.")
    else:
        response_data = response.get("choices", [{}])[0].get("message", {})
        ai_message = AIMessage(**response_data)
        
        if not ai_message.tool_calls and isinstance(ai_message.content, str):
            try:
                tool_call_data = json.loads(ai_message.content)
                if "name" in tool_call_data and "parameters" in tool_call_data:
                    print("📝 Manually parsing tool call from content...")
                    ai_message = AIMessage(
                        content="", 
                        tool_calls=[{
                            "name": tool_call_data["name"],
                            "args": tool_call_data["parameters"],
                            "id": f"call_{uuid.uuid4()}"
                        }]
                    )
            except (json.JSONDecodeError, TypeError):
                pass
    
    return {"messages": state['messages'] + [ai_message]}

def call_tool(state: AgentState):
    """Executes a tool call requested by the LLM."""
    last_message = state['messages'][-1]
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": state['messages']}

    tool_call = last_message.tool_calls[0]
    tool_name = tool_call['name']
    tool_args = tool_call['args']
    
    print(f"🛠️ Executing tool: {tool_name} with args {tool_args}")

    if isinstance(tool_args, str):
        try:
            tool_args = json.loads(tool_args)
        except json.JSONDecodeError:
            print(f"Error: Could not decode tool arguments: {tool_args}")
            tool_args = {}

    if tool_name in calculator_client.tools:
        result = calculator_client.call_tool(tool_name, **tool_args)
    else:
        result = f"Error: Tool '{tool_name}' not found."

    # THE FIX: Instead of a ToolMessage, create a HumanMessage with the result.
    # This is a more robust way to feed information back to the LLM.
    result_message = HumanMessage(
        content=f"The result of calling the '{tool_name}' tool is: {result}"
    )
    return {"messages": state['messages'] + [result_message]}


# --- Define the Conditional Edge ---

def should_continue(state: AgentState):
    """Decides whether to continue the loop or end."""
    last_message = state['messages'][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"

# --- Build the Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("llm", call_inference_model)
workflow.add_node("tools", call_tool)

workflow.set_entry_point("llm")

workflow.add_conditional_edges(
    "llm",
    should_continue,
    {
        "tools": "tools",
        "end": END,
    },
)

workflow.add_edge("tools", "llm")

agent_app = workflow.compile()

