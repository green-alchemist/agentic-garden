# clients/cli_agent/src/mcp_client.py
import requests
import time
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
        url = f"{self.server_url}/openapi.json"
        for i in range(5):
            try:
                response = requests.get(url)
                response.raise_for_status()
                schema = response.json()
                
                paths = schema.get("paths", {})
                
                # --- DIAGNOSTIC STEP: Print all discovered paths ---
                print(f"🕵️  Discovered API paths on {self.server_url}: {list(paths.keys())}")
                
                tool_schemas = {}
                for path, methods in paths.items():
                    # Standard MCP convention: tools are at /tools/{tool_name}
                    if path.startswith("/tools/"):
                        # Extract the final part of the path as the tool name
                        tool_name = path.split("/")[-1]
                        description = methods.get("post", {}).get("description", "No description.")
                        tool_schemas[tool_name] = {"description": description}

                print(f"✅ Discovered tools on {self.server_url}: {list(tool_schemas.keys())}")
                return tool_schemas

            except requests.exceptions.RequestException as e:
                print(f"⏳ Attempt {i+1}/5 failed for {self.server_url}: {e}. Retrying in 2s...")
                time.sleep(2)
        
        print(f"❌ Error discovering tools on {self.server_url} after 5 attempts.")
        return {}


    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call a specific tool on the MCP server with the given arguments."""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found on server {self.server_url}."
        
        try:
            # MCP convention is that tools are exposed at /tools/{tool_name}
            tool_url = f"{self.server_url}/tools/{tool_name}"
            response = requests.post(tool_url, json=kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return f"Error calling tool '{tool_name}': {e}"

