# AGENTIC GARDEN
Welcome to the Agentic Garden, a robust, multi-tool agentic framework designed for extensibility and real-world application. This project provides a solid foundation for building sophisticated agents that can reason, act, and solve complex problems by leveraging a variety of specialized tools.

## Core Architecture
The Agentic Garden is built on a microservices architecture, where each component is containerized with Docker and managed by Docker Compose. This design ensures a clean separation of concerns and allows for independent development and scaling of each part of the system.

graph TD
    subgraph User Interaction
        User[<fa:fa-user> User]
    end

    subgraph Agent Core
        CLI_Agent[<fa:fa-terminal> cli_agent]
    end

    subgraph Services
        Inference_Server[<fa:fa-brain> inference_server]
        Calculator_Server[<fa:fa-calculator> calculator_server]
        Other_Tools[<fa:fa-wrench> Other Tool Servers]
    end

    User -- "Sends Prompt" --> CLI_Agent
    CLI_Agent -- "1. Sends history for reasoning" --> Inference_Server
    Inference_Server -- "2. Returns decision (text or tool call)" --> CLI_Agent
    CLI_Agent -- "3. Executes tool call" --> Calculator_Server
    CLI_Agent -- "3. Executes tool call" --> Other_Tools
    Calculator_Server -- "4. Returns result" --> CLI_Agent
    Other_Tools -- "4. Returns result" --> CLI_Agent
    CLI_Agent -- "5. Sends result for final answer" --> Inference_Server
    Inference_Server -- "6. Returns final text answer" --> CLI_Agent
    CLI_Agent -- "Displays final answer" --> User

The primary components are:

inference_server: The "brain" of the operation. This service hosts a large language model (LLM) using llama-cpp-python and exposes it as a tool that the agent can call to reason and make decisions.

Tool Servers (e.g., calculator_server): These are specialized, single-purpose servers that provide the agent with its "hands." Each tool server exposes one or more functions (like add or subtract) that the agent can execute to interact with the world or perform specific tasks. The architecture is designed to support many of these, such as file indexers, web browsers, etc.

cli_agent: The central nervous system. This is the client application that orchestrates the entire process. It holds the agent's reasoning loop (built with LangGraph), manages the conversation history, and communicates with the inference and tool servers.

Getting Started
Follow these steps to get your own Agentic Garden up and running.

Prerequisites
Docker and Docker Compose: Ensure they are installed on your system.

NVIDIA GPU: The inference_server is configured to use an NVIDIA GPU for model acceleration. You must have the NVIDIA Container Toolkit installed.

1. Configuration
Before launching, you need to configure the model that the inference_server will use.

Create an environment file: In the root of the project, create a file named .env.

Specify the model: Add the following line to your .env file, replacing the placeholder with the name of the GGUF-format model you want to use. This model must support function calling.

MODEL_NAME=Meta-Llama-3.1-8B-Instruct.Q4_K_M.gguf

Download the model: Place the model file you specified into the services/inference_server/models/ directory.

2. Build and Run the Services
With the configuration in place, you can start all the services using Docker Compose.

docker compose up --build -d

This command will build the Docker images for each service and run them in the background.

3. Interact with the Agent
Once the services are running, you can start a conversation with the agent.

Attach to the agent's container:

docker compose exec cli_agent bash

Run the agent script:

python run.py

You will be greeted with a prompt, and you can start asking the agent questions. The agent will automatically discover and use the tools provided by the calculator_server.

Example Session:

🤖 Coding Assistant w/ Memory is ready. Type 'exit' to quit.
You: add 3 and 4
🧠 Thinking...
📝 Manually parsing tool call from content...
🛠️ Executing tool: add with args {'a': 3, 'b': 4}
🧠 Thinking...
Assistant: The result of adding 3 and 4 is 7.
--------------------
You: my name is kyle subtract that result from 99
🧠 Thinking...
📝 Manually parsing tool call from content...
🛠️ Executing tool: subtract with args {'a': 99, 'b': 7}
🧠 Thinking...
Assistant: The result of subtracting 7 from 99 is 92.

How It Works: The ReAct Loop
The agent uses a ReAct (Reasoning and Acting) loop, implemented with LangGraph. On each turn, the agent:

Thinks: The cli_agent sends the conversation history to the inference_server. The LLM decides whether it can answer directly or if it needs to use a tool.

Acts: If the LLM decides to use a tool, it returns a JSON object specifying the tool's name and parameters. The agent's ToolExecutor then calls the appropriate tool server (e.g., the calculator_server).

Observes: The result of the tool call is sent back to the inference_server. The LLM uses this new information to formulate a final, human-readable answer.

This loop continues until the agent can provide a complete answer to the user's query.

Next Steps
This project is a living framework. The next major step is to integrate a new tool server for file indexing and retrieval, allowing the agent to answer questions about the contents of local documents.