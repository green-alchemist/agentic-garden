# clients/cli_agent/src/tool_executor.py
import os
from typing import List, Dict, Any
from langchain_core.messages import ToolMessage

from .mcp_client import MCPClient

class ToolExecutor:
    """
    Handles the discovery, validation, and execution of all tools
    available to the agent from any connected MCP server.
    """
    def __init__(self):
        # --- Discover clients from environment variables ---
        self.inference_client = MCPClient(server_url="http://inference_server:8000")
        
        # This will expand as you add more tool servers
        self.tool_clients = {
            "calculator_client": MCPClient(server_url="http://calculator_server:8000"),
            # Add new clients here, e.g.:
            # "file_indexer_client": MCPClient(server_url="http://file_indexer:8000"),
        }
        
        # --- Build a unified map of all available tools ---
        self.tools_map = self._discover_all_tools()

    def _discover_all_tools(self) -> Dict[str, MCPClient]:
        """
        Creates a single dictionary mapping tool names to the client
        that can execute them.
        """
        unified_map = {}
        for client in self.tool_clients.values():
            for tool_name in client.tools:
                unified_map[tool_name] = client
        return unified_map

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Generates the tool schema list required by the LLM, combining
        schemas from all available clients.
        """
        llm_tools = []
        for client in self.tool_clients.values():
            # THE FIX: Access the tool_schemas dictionary directly
            llm_tools.extend(client.tool_schemas.values())
        return llm_tools

    def execute_tool(self, tool_call: Dict[str, Any]) -> ToolMessage:
        """
        Validates parameters and executes a given tool call.
        """
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        
        print(f"🛠️ Executing tool: {tool_name} with args {tool_args}")

        client = self.tools_map.get(tool_name)
        if not client:
            result = f"Error: Tool '{tool_name}' not found."
        else:
            # Basic validation can still happen here
            if not isinstance(tool_args, dict):
                 result = f"Error: Tool '{tool_name}' was called with invalid arguments. A dictionary of parameters is required."
            else:
                result = client.call_tool(tool_name, **tool_args)

        return ToolMessage(content=str(result), tool_call_id=tool_call['id'])

