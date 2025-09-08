# clients/cli_agent/src/mcp_client.py
import requests
from typing import List, Dict, Any
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MCPClient:
    """A client for discovering and calling tools on an MCP server."""

    def __init__(self, server_url: str):
        if not server_url.startswith("http"):
            raise ValueError("Server URL must include http:// or https://")
        self.server_url = server_url.rstrip('/')
        self.tools = self._discover_tools_with_retry()

    def _discover_tools_with_retry(self, retries=5, delay=2) -> Dict[str, Any]:
        """Fetch the list of available tools, retrying on connection errors."""
        for i in range(retries):
            try:
                # --- FIX: Re-added the /mcp path, which is now correct ---
                response = requests.get(f"{self.server_url}/openapi.json", verify=False)
                response.raise_for_status()
                schema = response.json()

                tool_schemas = {}
                paths = schema.get("paths", {})
                for path, methods in paths.items():
                    if path.startswith("/tools/"):
                        tool_name = path.split("/")[-1]
                        description = methods.get("post", {}).get("description", "No description.")
                        tool_schemas[tool_name] = {"description": description}
                print(f"✅ Discovered tools on {self.server_url}: {list(tool_schemas.keys())}")
                return tool_schemas
            except requests.exceptions.RequestException as e:
                print(f"⏳ Attempt {i+1}/{retries} failed for {self.server_url}: {e}. Retrying in {delay}s...")
                time.sleep(delay)
        
        print(f"❌ Error discovering tools on {self.server_url} after {retries} attempts.")
        return {}


    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call a specific tool on the MCP server with the given arguments."""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found on server {self.server_url}."

        try:
            # --- FIX: Re-added the /mcp path, which is now correct ---
            tool_url = f"{self.server_url}/tools/{tool_name}"
            response = requests.post(tool_url, json=kwargs, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return f"Error calling tool '{tool_name}': {e}"

