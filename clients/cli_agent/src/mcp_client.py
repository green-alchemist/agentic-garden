# clients/cli_agent/src/mcp_client.py
import requests
from typing import List, Dict, Any

class MCPClient:
    """A client for discovering and calling tools on an MCP server."""

    def __init__(self, server_url: str):
        if not server_url.startswith("http"):
            raise ValueError("Server URL must include http:// or https://")
        self.server_url = server_url.rstrip('/')
        self.tools = self._discover_tools()

    def _discover_tools(self) -> Dict[str, Any]:
        """Fetch the list of available tools from the server's OpenAPI spec."""
        try:
            response = requests.get(f"{self.server_url}/openapi.json")
            response.raise_for_status()
            schema = response.json()
            
            tool_schemas = {}
            paths = schema.get("paths", {})
            for path, methods in paths.items():
                if "/tools/" in path:
                    tool_name = path.split("/")[-1]
                    description = methods.get("post", {}).get("description", "No description.")
                    tool_schemas[tool_name] = {"description": description}
            print(f"✅ Discovered tools on {self.server_url}: {list(tool_schemas.keys())}")
            return tool_schemas
        except requests.exceptions.RequestException as e:
            print(f"❌ Error discovering tools on {self.server_url}: {e}")
            return {}

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call a specific tool on the MCP server with the given arguments."""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found on server {self.server_url}."
        
        try:
            tool_url = f"{self.server_url}/tools/{tool_name}"
            response = requests.post(tool_url, json=kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return f"Error calling tool '{tool_name}': {e}"