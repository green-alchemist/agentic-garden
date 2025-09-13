# MCP Server & Client Setup Guide

This setup provides a complete MCP (Model Context Protocol) server and client with support for multiple LLM types in a dockerized, ephemeral environment.

## Components

1. **MCP Server** - Provides tools/capabilities
2. **MCP Client** - Connects to server and LLMs  
3. **Bridge** - Orchestrates the connection
4. **Docker Setup** - For ephemeral deployment

## Quick Start

### 1. Basic Setup

```bash
# Create project directory
mkdir mcp-setup && cd mcp-setup

# Save the Python files from the artifacts above:
# - mcp_server.py
# - mcp_client.py  
# - bridge_runner.py

# Save Dockerfiles:
# - Dockerfile (for MCP server)
# - Dockerfile.bridge (for bridge)
# - docker-compose.yml
```

### 2. Environment Configuration

Create a `.env` file:

```bash
# LLM Configuration
LLM_TYPE=ollama  # or openai, anthropic
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Runtime options
INTERACTIVE=true
```

### 3. Run with Docker Compose

```bash
# Start all services
docker-compose up --build

# For background running
docker-compose up -d --build

# View logs
docker-compose logs -f mcp-bridge
```

### 4. Local Development

```bash
# Install dependencies
pip install aiohttp

# Run MCP server locally
python mcp_server.py &

# Run client with local LLM
LLM_TYPE=ollama python mcp_client.py

# Or with API-based LLM
LLM_TYPE=openai OPENAI_API_KEY=your_key python mcp_client.py
```

## LLM Options

### Ollama (Local)
- Runs locally with privacy
- Requires model download
- Good for development/testing

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2
```

### OpenAI API
- High quality responses
- Requires API key and credits
- Fast inference

### Anthropic Claude
- Advanced reasoning
- Requires API key
- Good for complex tasks

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│   MCP Server    │    │      LLM        │
│   (Bridge)      │    │   (Tools)       │    │  (Ollama/API)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Available Tools

The example server provides:

- **get_time** - Get current timestamp
- **execute_command** - Run shell commands safely  
- **list_files** - List directory contents

## Customization

### Adding New Tools

In `mcp_server.py`, add to the `tools` dictionary:

```python
"my_tool": {
    "name": "my_tool",
    "description": "Description of what the tool does",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param1"]
    }
}
```

Then implement the handler:

```python
async def my_tool_handler(self, param1: str) -> str:
    # Your tool logic here
    return f"Result: {param1}"

# Add to handle_request method:
elif tool_name == "my_tool":
    result = await self.my_tool_handler(arguments.get("param1"))
```

### Integrating External APIs

Example of adding a weather tool:

```python
async def get_weather(self, location: str) -> str:
    async with aiohttp.ClientSession() as session:
        url = f"https://api.weather.com/v1/current?location={location}"
        async with session.get(url) as response:
            data = await response.json()
            return f"Weather in {location}: {data['weather']}"
```

### Custom LLM Integration

Add your own LLM in `mcp_client.py`:

```python
async def _call_custom_llm(self, messages: List[Dict]) -> str:
    # Your LLM integration here
    # Could be transformers, llama.cpp, etc.
    pass
```

## Production Considerations

### Security
- Review and restrict the `execute_command` tool
- Add input validation and sanitization
- Use proper authentication for external APIs
- Limit network access in containers

### Scaling
- Use Redis for session storage
- Implement horizontal scaling
- Add load balancing
- Monitor resource usage

### Monitoring
```bash
# Check container health
docker-compose ps

# Monitor logs
docker-compose logs -f --tail=100

# Resource usage
docker stats
```

## Troubleshooting

### Common Issues

**1. Ollama connection failed**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Pull a model if none available
ollama pull llama2
```

**2. MCP Server not responding**
```bash
# Check server logs
docker-compose logs mcp-server

# Test server directly
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python mcp_server.py
```

**3. Bridge connection issues**
```bash
# Check network connectivity
docker-compose exec mcp-bridge nc -z mcp-server 8000
docker-compose exec mcp-bridge nc -z ollama 11434
```

**4. API Key issues**
- Ensure `.env` file is in the right directory
- Check API key validity
- Verify environment variable loading

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Usage

### HTTP Transport

For production use, implement HTTP transport instead of stdin/stdout:

```python
# In mcp_server.py
from aiohttp import web

async def handle_mcp_request(request):
    data = await request.json()
    response = await server.handle_request(data)
    return web.json_response(response)

app = web.Application()
app.router.add_post('/mcp', handle_mcp_request)
web.run_app(app, port=8000)
```

### Multi-Tool Workflows

Example of chaining tools:

```python
# Get file list, then process each file
files_result = await client.call_tool("list_files", {"path": "/data"})
for file in parse_files(files_result):
    result = await client.call_tool("process_file", {"file": file})
```

### Custom Protocol Extensions

Extend MCP with custom methods:

```python
# Custom notification
await client.send_request("custom/notify", {"message": "Task complete"})

# Custom streaming
async for chunk in client.stream_request("custom/stream", params):
    process_chunk(chunk)
```

## API Reference

### MCP Server Methods
- `initialize` - Initialize connection
- `tools/list` - Get available tools
- `tools/call` - Execute a tool

### Client Configuration
```python
LLMConfig(
    type="ollama|openai|anthropic|local",
    model="model_name",
    api_key="optional_api_key",
    base_url="optional_base_url",
    temperature=0.7,
    max_tokens=2000
)
```

### Docker Environment Variables
- `LLM_TYPE` - Type of LLM to use
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `OLLAMA_HOST` - Ollama server URL
- `INTERACTIVE` - Enable interactive mode
- `MCP_SERVER_HOST` - MCP server hostname

This setup provides a complete foundation for building MCP-based applications with flexible LLM integration and containerized deployment.