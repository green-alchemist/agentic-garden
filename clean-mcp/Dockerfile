FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy server code
COPY mcp_server.py .

# Make server executable
RUN chmod +x mcp_server.py

# Expose port for communication (if using HTTP transport)
EXPOSE 8000

# Default command
CMD ["python", "mcp_server.py"]