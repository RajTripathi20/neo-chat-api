from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
import json

# Import services
from src.services.authentication import verify_api_key
from src.services.rate_limiter import check_rate_limit
from src.models.api_models import ChatRequest, ChatResponse, Message, Choice, Usage, ModelsResponse, ModelInfo, ModelPricing
from src.utils.constants.api import (
    CHAT_COMPLETIONS_PATH, 
    MODELS_PATH, 
    STREAM_END_MARKER
)
from src.utils.constants.models import (
    REASONING_MODEL_ID,
    DEFAULT_INCLUDE_REASONING, 
    DEFAULT_REASONING_EFFORT,
    VALID_REASONING_EFFORTS,
    AVAILABLE_MODELS
)

"""
OpenAI-compatible API router.

This module provides API endpoints that are compatible with the OpenAI API,
allowing clients to use this service as a drop-in replacement for OpenAI.
"""

router = APIRouter()

@router.post(CHAT_COMPLETIONS_PATH, response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    req: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    OpenAI-compatible chat completion endpoint.
    
    This endpoint processes chat completion requests and returns responses
    in the same format as the OpenAI API.
    
    Args:
        request: The chat completion request.
        req: The FastAPI request object.
        api_key: The API key (verified by the dependency).
        
    Returns:
        ChatResponse: The chat completion response.
    """
    # Check rate limit
    await check_rate_limit(api_key)
    
    # Handle reasoning parameters for neo-reasoning model
    if request.model == REASONING_MODEL_ID:
        # Default to include_reasoning=True for neo-reasoning model if not specified
        if request.include_reasoning is None:
            request.include_reasoning = DEFAULT_INCLUDE_REASONING
        
        # Default to medium reasoning_effort if not specified
        if request.reasoning_effort is None:
            request.reasoning_effort = DEFAULT_REASONING_EFFORT
        
        # Validate reasoning_effort parameter
        if request.reasoning_effort not in VALID_REASONING_EFFORTS:
            request.reasoning_effort = DEFAULT_REASONING_EFFORT
    
    # Process request through pipeline
    from src.processing.pipeline import process_request, process_streaming_request
    
    # Handle streaming response
    if request.stream:
        return StreamingResponse(
            content=stream_response(request, process_streaming_request),
            media_type="text/event-stream"
        )
    
    # Return standard response
    result = await process_request(request)
    return result

@router.get(MODELS_PATH, response_model=ModelsResponse)
async def list_models(
    req: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    OpenAI-compatible models endpoint.
    
    This endpoint returns a list of available models in the same format
    as the OpenAI API.
    
    Args:
        req: The FastAPI request object.
        api_key: The API key (verified by the dependency).
        
    Returns:
        ModelsResponse: The models response.
    """
    # Define available models
    models = []
    for model_data in AVAILABLE_MODELS:
        models.append(
            ModelInfo(
                id=model_data["id"],
                name=model_data["name"],
                description=model_data["description"],
                pricing=ModelPricing(
                    input_price_per_million_tokens=model_data["input_price_per_million_tokens"],
                    output_price_per_million_tokens=model_data["output_price_per_million_tokens"]
                ),
                context_length=model_data["context_length"]
            )
        )
    
    # Return models response
    return ModelsResponse(data=models)

async def stream_response(request: ChatRequest, processor):
    """
    Stream the response in SSE format.
    
    Args:
        request: The chat completion request.
        processor: The function to process the streaming request.
        
    Yields:
        str: Chunks of the response in SSE format.
    """
    async for chunk in processor(request):
        # Convert the chunk to JSON
        chunk_json = chunk.json()
        
        # Yield the chunk in SSE format
        yield f"data: {chunk_json}\n\n"
    
    # Signal the end of the stream
    yield STREAM_END_MARKER 