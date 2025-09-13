#!/usr/bin/env python3
"""
MCP Client with support for local and API-based LLMs
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional
import aiohttp
import os
from dataclasses import dataclass

@dataclass
class LLMConfig:
    type: str  # 'local', 'openai', 'anthropic', 'ollama'
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000

class MCPClient:
    def __init__(self, server_command: List[str], llm_config: LLMConfig):
        self.server_command = server_command
        self.llm_config = llm_config
        self.server_process = None
        self.request_id = 0
        self.available_tools = []

    def get_next_id(self) -> int:
        self.request_id += 1
        return self.request_id

    async def start_server(self):
        """Start the MCP server process"""
        self.server_process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print("MCP Server started")

    async def stop_server(self):
        """Stop the MCP server process"""
        if self.server_process:
            self.server_process.terminate()
            await self.server_process.wait()

    async def send_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Send request to MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": self.get_next_id(),
            "method": method,
            "params": params or {}
        }

        request_json = json.dumps(request) + '\n'
        self.server_process.stdin.write(request_json.encode())
        await self.server_process.stdin.drain()

        response_line = await self.server_process.stdout.readline()
        return json.loads(response_line.decode())

    async def initialize(self):
        """Initialize connection with MCP server"""
        response = await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-client",
                "version": "1.0.0"
            }
        })
        
        # Get available tools
        tools_response = await self.send_request("tools/list")
        self.available_tools = tools_response.get("result", {}).get("tools", [])
        
        print(f"Initialized with {len(self.available_tools)} tools")
        return response

    async def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """Call a tool on the MCP server"""
        response = await self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        if "error" in response:
            return f"Error: {response['error']['message']}"
        
        content = response.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            return content[0].get("text", "")
        
        return "No response"

    async def call_llm(self, messages: List[Dict[str, str]], tools_context: str = "") -> str:
        """Call LLM with optional tools context"""
        
        # Add tools context to system message if available
        if tools_context and self.available_tools:
            tools_info = "\n".join([
                f"- {tool['name']}: {tool['description']}" 
                for tool in self.available_tools
            ])
            system_msg = f"You have access to these tools:\n{tools_info}\n\nUse tools when helpful. {tools_context}"
            
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] = system_msg + "\n\n" + messages[0]["content"]
            else:
                messages.insert(0, {"role": "system", "content": system_msg})

        if self.llm_config.type == "openai":
            return await self._call_openai(messages)
        elif self.llm_config.type == "anthropic":
            return await self._call_anthropic(messages)
        elif self.llm_config.type == "ollama":
            return await self._call_ollama(messages)
        elif self.llm_config.type == "local":
            return await self._call_local_llm(messages)
        else:
            return "Unsupported LLM type"

    async def _call_openai(self, messages: List[Dict]) -> str:
        """Call OpenAI API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.llm_config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.llm_config.model,
                "messages": messages,
                "temperature": self.llm_config.temperature,
                "max_tokens": self.llm_config.max_tokens
            }
            
            base_url = self.llm_config.base_url or "https://api.openai.com/v1"
            
            async with session.post(f"{base_url}/chat/completions", 
                                  headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"API Error: {response.status}"

    async def _call_anthropic(self, messages: List[Dict]) -> str:
        """Call Anthropic API"""
        # Extract system message if present
        system_content = ""
        filtered_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                filtered_messages.append(msg)
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": self.llm_config.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": self.llm_config.model,
                "messages": filtered_messages,
                "max_tokens": self.llm_config.max_tokens,
                "temperature": self.llm_config.temperature
            }
            
            if system_content:
                payload["system"] = system_content
            
            async with session.post("https://api.anthropic.com/v1/messages",
                                  headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["content"][0]["text"]
                else:
                    return f"API Error: {response.status}"

    async def _call_ollama(self, messages: List[Dict]) -> str:
        """Call Ollama local API"""
        async with aiohttp.ClientSession() as session:
            base_url = self.llm_config.base_url or "http://localhost:11434"
            
            payload = {
                "model": self.llm_config.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.llm_config.temperature,
                    "num_predict": self.llm_config.max_tokens
                }
            }
            
            async with session.post(f"{base_url}/api/chat", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["message"]["content"]
                else:
                    return f"Ollama Error: {response.status}"

    async def _call_local_llm(self, messages: List[Dict]) -> str:
        """Call local LLM (placeholder - implement based on your local setup)"""
        # This is a placeholder for local LLM integration
        # You might use transformers, llama.cpp, etc.
        return "Local LLM not implemented - add your local LLM integration here"

    async def chat_loop(self):
        """Interactive chat loop with tool calling capability"""
        print("MCP Client with LLM integration started!")
        print("Available tools:", [tool['name'] for tool in self.available_tools])
        print("Type 'quit' to exit, 'tools' to list tools\n")
        
        conversation = []
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'tools':
                for tool in self.available_tools:
                    print(f"- {tool['name']}: {tool['description']}")
                continue
            
            # Add user message to conversation
            conversation.append({"role": "user", "content": user_input})
            
            # Get LLM response
            llm_response = await self.call_llm(
                conversation, 
                "If the user request requires using tools, suggest which tools to use and how."
            )
            
            print(f"Assistant: {llm_response}")
            
            # Check if response suggests tool usage
            if any(tool['name'] in llm_response.lower() for tool in self.available_tools):
                tool_prompt = input("Execute suggested tools? (y/n): ").strip().lower()
                if tool_prompt == 'y':
                    # Simple tool execution example
                    for tool in self.available_tools:
                        if tool['name'] in llm_response.lower():
                            if tool['name'] == 'get_time':
                                result = await self.call_tool('get_time', {})
                                print(f"Tool result: {result}")
                            # Add more tool handling as needed
            
            # Add assistant response to conversation
            conversation.append({"role": "assistant", "content": llm_response})
            
            # Keep conversation manageable
            if len(conversation) > 20:
                conversation = conversation[-10:]

async def main():
    # Configuration examples
    llm_configs = {
        "ollama": LLMConfig(
            type="ollama",
            model="llama2",  # or any model you have in Ollama
            base_url="http://localhost:11434"
        ),
        "openai": LLMConfig(
            type="openai", 
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY")
        ),
        "anthropic": LLMConfig(
            type="anthropic",
            model="claude-3-sonnet-20240229", 
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    }
    
    # Choose your LLM
    llm_type = os.getenv("LLM_TYPE", "ollama")
    llm_config = llm_configs.get(llm_type)
    
    if not llm_config:
        print(f"Invalid LLM type: {llm_type}")
        return
    
    # Server command - adjust based on your setup
    server_command = ["python", "mcp_server.py"]  # or ["docker", "run", "mcp-server"]
    
    client = MCPClient(server_command, llm_config)
    
    try:
        await client.start_server()
        await client.initialize()
        await client.chat_loop()
    finally:
        await client.stop_server()

if __name__ == "__main__":
    asyncio.run(main())