# Placeholder for gsheets_server main.py
# We will implement the MCP server logic here in the next step.
from fastapi import FastAPI

app = FastAPI(title="Google Sheets MCP Server")

@app.get("/")
def read_root():
    return {"status": "ok", "service": "gsheets_server"}
