FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ .

EXPOSE 8000

# FIX: Point Uvicorn to 'main:mcp' to match the new file structure.
CMD ["uvicorn", "main:mcp", "--host", "0.0.0.0", "--port", "8000"]

