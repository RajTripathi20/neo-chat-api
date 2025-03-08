from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json

# Import services
from src.services.authentication import verify_api_key
from src.services.rate_limiter import check_rate_limit
from src.models.api_models import ChatRequest, ChatResponse, Message, Choice, Usage

router = APIRouter()

@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    req: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    OpenAI-compatible chat completion endpoint
    """
    # Check rate limit
    await check_rate_limit(api_key)
    
    # Process request through pipeline
    from src.processing.pipeline import process_request
    result = await process_request(request)
    
    # Handle streaming response
    if request.stream:
        return StreamingResponse(
            content=stream_response(result),
            media_type="text/event-stream"
        )
    
    # Return standard response
    return result

async def stream_response(result):
    """
    Stream the response in SSE format
    """
    # This is a placeholder for the actual streaming implementation
    yield f"data: {json.dumps(result.dict())}\n\n"
    yield "data: [DONE]\n\n" 