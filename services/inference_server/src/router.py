from fastapi import APIRouter
from .schemas import QueryRequest, QueryResponse
from .inference import get_coding_assistant_chain
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/invoke", response_model=QueryResponse)
async def invoke_agent(request: QueryRequest):
    logger.info(f"Received query: {request.query}")
    chain = get_coding_assistant_chain()
    result = chain.invoke({"input": request.query})
    
    # Assuming the result has an 'output' key
    # You may need to adjust this based on your chain's actual output structure
    response_content = result.get("output", "No output found.")
    
    logger.info(f"Generated response: {response_content}")
    return QueryResponse(response=response_content)