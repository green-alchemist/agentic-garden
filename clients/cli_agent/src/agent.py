# clients/cli_agent/src/agent.py
import os
import json
import uuid
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage

from .mcp_client import MCPClient

# --- Connect to our MCP servers ---
inference_client = MCPClient(server_url="http://inference_server:8000")
calculator_client = MCPClient(server_url="http://calculator_server:8000")

# --- Define the Agent's State ---
class AgentState(TypedDict):
    messages: List[BaseMessage]

# --- Define the Tools for the LLM ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "Adds two numbers together.",
            "parameters": {
                "type": "object",
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
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
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                "required": ["a", "b"],
            },
        },
    }
]

# --- Helper function for role mapping ---
def map_message_to_api(message: BaseMessage) -> Dict[str, Any]:
    role_map = {"human": "user", "ai": "assistant", "tool": "tool"}
    role = role_map.get(message.type, "user")
    
    if isinstance(message, AIMessage):
        data = {"role": role, "content": message.content or None}
        if message.tool_calls:
            # Transform LangChain's tool_calls format to the one expected by llama-cpp-python.
            transformed_tool_calls = []
            for tc in message.tool_calls:
                transformed_tool_calls.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["args"]) # Arguments must be a JSON string
                    }
                })
            data["tool_calls"] = transformed_tool_calls
        return data
    
    if isinstance(message, ToolMessage):
        return {
            "role": role,
            "content": message.content,
            "tool_call_id": message.tool_call_id
        }

    return {"role": role, "content": message.content}

# --- Agent's Nodes (Actions) ---

def call_inference_model(state: AgentState):
    print("🧠 Thinking...")
    messages_for_api = [map_message_to_api(msg) for msg in state['messages']]
    
    last_message = state['messages'][-1]
    should_send_tools = not isinstance(last_message, ToolMessage)

    kwargs = {
        "messages": messages_for_api,
        "temperature": 0,
    }
    if should_send_tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = inference_client.call_tool("create_chat_completion", **kwargs)
    
    if isinstance(response, str):
        print(f"Error from server: {response}")
        ai_message = AIMessage(content="I'm sorry, I encountered an error. Please check the logs.")
    else:
        response_data = response.get("choices", [{}])[0].get("message", {})
        
        # When a tool call is present, create a clean AIMessage with no content.
        # This prevents the raw JSON tool call from polluting the chat history.
        if response_data.get("tool_calls"):
            ai_message = AIMessage(content="", tool_calls=response_data["tool_calls"])
        else:
            # This is a regular message
            ai_message = AIMessage(**response_data)
        
        # This block is still needed for models that put the tool call in the content field
        if not ai_message.tool_calls and isinstance(ai_message.content, str):
            try:
                tool_call_data = json.loads(ai_message.content)
                if "name" in tool_call_data and "parameters" in tool_call_data:
                    print("📝 Manually parsing tool call from content...")
                    
                    # Ensure the 'parameters' (which become 'args') is a dictionary.
                    # Some models return it as a string, so we parse it if needed.
                    params = tool_call_data["parameters"]
                    if isinstance(params, str):
                        params = json.loads(params)

                    ai_message = AIMessage(
                        content="", 
                        tool_calls=[{
                            "name": tool_call_data["name"],
                            "args": params,
                            "id": f"call_{uuid.uuid4()}"
                        }]
                    )
            except (json.JSONDecodeError, TypeError):
                pass
    
    return {"messages": state['messages'] + [ai_message]}

def call_tool(state: AgentState):
    last_message = state['messages'][-1]
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": state['messages']}

    tool_call = last_message.tool_calls[0]
    tool_name = tool_call['name']
    tool_args = tool_call['args']
    
    print(f"🛠️ Executing tool: {tool_name} with args {tool_args}")

    # THE FIX: Add a validation layer before calling the calculator tool.
    if tool_name in ["add", "subtract"]:
        try:
            # Ensure args are numbers before calling the tool
            a = float(tool_args.get("a", 0))
            b = float(tool_args.get("b", 0))
            result = calculator_client.call_tool(tool_name, a=a, b=b)
        except (ValueError, TypeError):
            # If args are not numbers, send an error message back to the LLM
            result = f"Error: Invalid parameters for tool '{tool_name}'. Parameters must be numbers."
    elif tool_name in calculator_client.tools:
        # This is a fallback for other potential calculator tools
        result = calculator_client.call_tool(tool_name, **tool_args)
    else:
        result = f"Error: Tool '{tool_name}' not found."

    tool_message = ToolMessage(content=str(result), tool_call_id=tool_call['id'])
    return {"messages": state['messages'] + [tool_message]}

# --- Conditional Edge ---

def should_continue(state: AgentState):
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
    {"tools": "tools", "end": END},
)
workflow.add_edge("tools", "llm")
agent_app = workflow.compile()

