#!/bin/bash

# A script to refactor the Agentic Garden project into a clean
# services-and-clients microservice architecture.

echo "🌱 Starting the architectural refactoring..."

# --- Step 1: Restructure Folders ---
echo "STEP 1: Restructuring directories..."

# Create the new clients directory structure
mkdir -p ./clients/cli_agent/src
echo "  - Created clients/cli_agent/src/"

# Move the existing agent code to its new home in the client service
# We use '|| true' to prevent errors if the source files don't exist
mv ./services/agents/coding_assistant.py ./clients/cli_agent/src/agent.py || true
mv ./services/agents/run_agent.py ./clients/cli_agent/run.py || true
echo "  - Moved agent logic to clients/cli_agent/"

# Remove the old, now-empty agents directory
rm -rf ./services/agents
echo "  - Removed old services/agents/ directory."

# Rename the inference engine for consistency
mv ./services/inference-engine ./services/inference_server || true
echo "  - Renamed services/inference-engine/ to services/inference_server/"


# --- Step 2: Create the Master docker-compose.yml ---
echo "STEP 2: Creating the master docker-compose.yml orchestrator..."

# Use a 'here document' (cat <<EOF) to write the multi-line file content.
cat > ./docker-compose.yml << EOF
version: '3.8'

services:
  inference_server:
    build:
      context: ./services/inference_server
    image: agentic-garden/inference-server
    volumes:
      - ./models:/app/models
    environment:
      - MODEL_NAME=\${MODEL_NAME}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  gsheets_server:
    build:
      context: ./services/gsheets_server
    image: agentic-garden/gsheets-server
    ports:
      - "8082:8000" # Expose the gsheets tool on your local machine
    volumes:
      - ./secrets:/app/secrets

  cli_agent:
    build:
      context: ./clients/cli_agent
    image: agentic-garden/cli-agent
    depends_on:
      - inference_server
      - gsheets_server
    command: tail -f /dev/null # Keep container running for exec
    volumes:
      - ./clients/cli_agent/src:/app/src
    environment:
      - INFERENCE_API_URL=http://inference_server:8000/v1/chat/completions
      - GSHEETS_API_URL=http://gsheets_server:8000
EOF
echo "  - Master docker-compose.yml created successfully."


# --- Step 3: Set up the new gsheets_server Service ---
echo "STEP 3: Scaffolding the new gsheets_server..."

mkdir -p ./services/gsheets_server/src
echo "  - Created services/gsheets_server/src/ directory."

# Create the Dockerfile for the gsheets service
cat > ./services/gsheets_server/Dockerfile << EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
echo "  - Created gsheets_server/Dockerfile."

# Create the requirements.txt for the gsheets service
cat > ./services/gsheets_server/requirements.txt << EOF
fastapi
uvicorn[standard]
pydantic
mcp[cli]
gspread
oauth2client
EOF
echo "  - Created gsheets_server/requirements.txt."

# Create a placeholder main.py for the gsheets service
cat > ./services/gsheets_server/src/main.py << EOF
# Placeholder for gsheets_server main.py
# We will implement the MCP server logic here in the next step.
from fastapi import FastAPI

app = FastAPI(title="Google Sheets MCP Server")

@app.get("/")
def read_root():
    return {"status": "ok", "service": "gsheets_server"}
EOF
echo "  - Created placeholder gsheets_server/src/main.py."


# --- Step 4: Set up the new cli_agent Client ---
echo "STEP 4: Scaffolding the new cli_agent client..."

# Create the Dockerfile for the agent
cat > ./clients/cli_agent/Dockerfile << EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["tail", "-f", "/dev/null"]
EOF
echo "  - Created cli_agent/Dockerfile."

# Create the requirements.txt for the agent
cat > ./clients/cli_agent/requirements.txt << EOF
langchain
langgraph
requests
langchain-core
mcp[cli] # Add MCP for tool use
EOF
echo "  - Created cli_agent/requirements.txt."

echo "✅ Architectural refactoring complete!"
echo "Run 'docker-compose up --build' to start your new multi-service system."