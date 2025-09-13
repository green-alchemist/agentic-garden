#!/usr/bin/env python3
"""
Bridge runner to connect MCP server with external tools/services
"""

import asyncio
import os
import sys
import time
import subprocess
from mcp_client import MCPClient, LLMConfig

async def wait_for_service(host: str, port: int, timeout: int = 30):
    """Wait for a service to be available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Use netcat to check if service is available
            result = subprocess.run(
                ['nc', '-z', host, str(port)], 
                capture_output=True, 
                timeout=5
            )
            if result.returncode == 0:
                print(f"Service {host}:{port} is available")
                return True
        except subprocess.TimeoutExpired:
            pass
        
        await asyncio.sleep(2)
    
    print(f"Service {host}:{port} is not available after {timeout}s")
    return False

async def setup_ollama_models():
    """Setup Ollama models if needed"""
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    try:
        # Check if ollama is available
        result = subprocess.run(['curl', '-s', f'{ollama_host}/api/tags'], 
                              capture_output=True, timeout=10)
        
        if result.returncode == 0:
            print("Ollama is available")
            # Optionally pull a model if none exist
            # subprocess.run(['curl', '-X', 'POST', f'{ollama_host}/api/pull', 
            #                '-d', '{"name":"llama2"}'], timeout=300)
        
    except Exception as e:
        print(f"Error setting up Ollama: {e}")

async def run_bridge():
    """Run the MCP bridge"""
    
    # Wait for dependent services
    mcp_server_host = os.getenv("MCP_SERVER_HOST", "localhost")
    ollama_host_url = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    
    # Extract host from URL for connectivity check
    ollama_host = ollama_host_url.replace("http://", "").replace("https://", "").split(":")[0]
    
    print("Waiting for services to be ready...")
    
    # Wait for Ollama if using it
    llm_type = os.getenv("LLM_TYPE", "ollama")
    if llm_type == "ollama":
        if not await wait_for_service(ollama_host, 11434):
            print("Ollama not available, continuing anyway...")
    
    # Setup LLM configuration
    llm_configs = {
        "ollama": LLMConfig(
            type="ollama",
            model="llama2",
            base_url=ollama_host_url
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
    
    llm_config = llm_configs.get(llm_type)
    if not llm_config:
        print(f"Invalid LLM type: {llm_type}")
        return
    
    # Setup MCP server command
    # In containerized environment, we might connect via network
    if mcp_server_host != "localhost":
        # Network connection to containerized MCP server
        # This would require implementing network transport in MCP client
        server_command = ["nc", mcp_server_host, "8000"]  # placeholder
    else:
        # Local execution
        server_command = ["python", "mcp_server.py"]
    
    print(f"Starting MCP Bridge with LLM: {llm_type}")
    
    client = MCPClient(server_command, llm_config)
    
    try:
        await client.start_server()
        await asyncio.sleep(2)  # Give server time to start
        await client.initialize()
        
        # Run interactive loop or API server
        interactive = os.getenv("INTERACTIVE", "true").lower() == "true"
        
        if interactive:
            await client.chat_loop()
        else:
            # Keep running for API access
            print("Bridge running in API mode...")
            while True:
                await asyncio.sleep(60)
                
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await client.stop_server()

if __name__ == "__main__":
    asyncio.run(run_bridge())