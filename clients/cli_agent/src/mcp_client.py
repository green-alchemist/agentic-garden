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
        self.tools = {}
        self.tool_schemas = {}
        self._discover_tools()

    def _discover_tools(self) -> None:
        """
        Fetch the list of available tools from the server's OpenAPI spec
        with a retry mechanism.
        """
        for i in range(5):
            try:
                response = requests.get(f"{self.server_url}/openapi.json")
                response.raise_for_status()
                schema = response.json()
                
                print(f"🕵️  Discovered API paths on {self.server_url}: {list(schema.get('paths', {}).keys())}")

                for path, methods in schema.get("paths", {}).items():
                    if path.startswith("/tools/"):
                        tool_name = path.split("/")[-1]
                        post_method = methods.get("post", {})
                        
                        self.tools[tool_name] = post_method
                        
                        # Generate the schema for the LLM
                        request_body = post_method.get("requestBody", {})
                        schema_ref = request_body.get("content", {}).get("application/json", {}).get("schema", {})
                        
                        # Follow the $ref to get the actual schema if it exists
                        if "$ref" in schema_ref:
                            ref_path = schema_ref["$ref"].split('/')[1:] # e.g., ['components', 'schemas', 'MyModel']
                            component_schema = schema
                            for part in ref_path:
                                component_schema = component_schema.get(part, {})
                            parameters = component_schema
                        else:
                            parameters = {}

                        self.tool_schemas[tool_name] = {
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "description": post_method.get("summary") or post_method.get("description", "No description."),
                                "parameters": parameters
                            }
                        }

                print(f"✅ Discovered tools on {self.server_url}: {list(self.tools.keys())}")
                return
            except requests.exceptions.RequestException as e:
                print(f"⏳ Attempt {i+1}/5 failed for {self.server_url}: {e}. Retrying in 2s...")
                time.sleep(2)
        print(f"❌ Error discovering tools on {self.server_url} after 5 attempts.")

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Returns the list of tool schemas for the LLM."""
        return list(self.tool_schemas.values())

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
            # Return the full error for better debugging
            return f"Error calling tool '{tool_name}': {e}"

