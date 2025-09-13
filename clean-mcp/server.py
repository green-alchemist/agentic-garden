#!/usr/bin/env python3
"""
Example MCP Server with basic tools for ephemeral use
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime
import subprocess
import os

class MCPServer:
    def __init__(self):
        self.tools = {
            "get_time": {
                "name": "get_time",
                "description": "Get current time",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "execute_command": {
                "name": "execute_command", 
                "description": "Execute a shell command safely",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Command to execute"
                        }
                    },
                    "required": ["command"]
                }
            },
            "list_files": {
                "name": "list_files",
                "description": "List files in a directory",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list"
                        }
                    },
                    "required": ["path"]
                }
            }
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request"""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "example-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }

            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0", 
                    "id": request_id,
                    "result": {
                        "tools": list(self.tools.values())
                    }
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "get_time":
                    result = await self.get_time()
                elif tool_name == "execute_command":
                    result = await self.execute_command(arguments.get("command"))
                elif tool_name == "list_files":
                    result = await self.list_files(arguments.get("path"))
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": str(result)
                            }
                        ]
                    }
                }

            else:
                raise ValueError(f"Unknown method: {method}")

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id, 
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            }

    async def get_time(self) -> str:
        """Get current time"""
        return f"Current time: {datetime.now().isoformat()}"

    async def execute_command(self, command: str) -> str:
        """Execute shell command safely"""
        # Basic safety check
        if any(dangerous in command.lower() for dangerous in ['rm -rf', 'rm -r /', 'dd if=', '> /dev']):
            return "Command blocked for safety"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return f"Exit code: {result.returncode}\nOutput: {result.stdout}\nError: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    async def list_files(self, path: str) -> str:
        """List files in directory"""
        try:
            if not os.path.exists(path):
                return f"Path does not exist: {path}"
            
            files = os.listdir(path)
            return f"Files in {path}:\n" + "\n".join(files)
        except Exception as e:
            return f"Error listing files: {str(e)}"

    async def run(self):
        """Run the MCP server"""
        print("MCP Server starting...", file=sys.stderr)
        
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = await self.handle_request(request)
                
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Server error: {e}", file=sys.stderr)

if __name__ == "__main__":
    server = MCPServer()
    asyncio.run(server.run())