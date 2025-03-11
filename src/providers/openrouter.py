"""
OpenRouter API client module.

This module provides a client for interacting with the OpenRouter API,
which allows routing requests to various AI models.
"""

import os
import json
import httpx
import asyncio
from typing import Dict, Any, List, AsyncGenerator, Optional
from dotenv import load_dotenv
from src.models.api_models import ChatRequest
from src.utils.constants.messages import ROLE_ASSISTANT
from src.utils.constants.models import (
    REASONING_MODEL_ID, DEFAULT_REASONING_EFFORT,
    VALID_REASONING_EFFORTS, OPENROUTER_GENERAL_MODEL, OPENROUTER_REASONING_MODELS
)
from src.utils.constants.server import (
    OPENROUTER_BASE_URL, OPENROUTER_REFERER, OPENROUTER_TITLE
)
from src.utils.constants.errors import ERROR_OPENROUTER_API

# Load environment variables
load_dotenv()

class RouterClient:
    """
    Client for the OpenRouter API.
    
    This client is configured to use only open source models.
    For reasoning capabilities, we use different models based on the
    requested reasoning effort level.
    
    We do not use proprietary models like OpenAI's o3.
    """
    
    def __init__(self):
        """
        Initialize the OpenRouter client with API key and headers.
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = OPENROUTER_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": OPENROUTER_REFERER,
            "X-Title": OPENROUTER_TITLE
        }
    
    async def get_generation_cost(self, generation_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed cost and usage information for a specific generation.
        
        Args:
            generation_id: The ID of the generation to retrieve information for.
            
        Returns:
            Dict[str, Any]: Cost and usage information.
            
        Raises:
            Exception: If the API request fails.
        """
        # TODO: Fix "Generation not found" error
        # The API is returning "Generation gen-XXXX not found" errors
        # Possible causes:
        # 1. Timing issue - trying to fetch cost info too quickly after generation
        # 2. API limitations - some generations might not be tracked properly
        # 3. Need to implement retry logic with backoff
        # 4. Consider implementing a fallback mechanism to estimate costs when API fails
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/generation?id={generation_id}",
                headers=self.headers,
                timeout=30.0
            )
            
            # Check for errors
            if response.status_code != 200:
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                raise Exception(f"{ERROR_OPENROUTER_API}: {error_detail}")
            
            # Parse the response
            result = response.json()
            
            # Extract cost information
            cost = result.get("cost", {})
            prompt_cost = cost.get("prompt", 0)
            completion_cost = cost.get("completion", 0)
            total_cost = prompt_cost + completion_cost
            
            # Extract usage information
            usage = result.get("usage", {})
            
            return {
                "cost": total_cost,
                "usage": usage,
                "model": result.get("model", "unknown"),
                "provider": result.get("provider", "unknown"),
                "generation_id": result.get("id", "unknown")
            }
    
    async def chat(self, request: ChatRequest) -> Dict[str, Any]:
        """
        Send a chat completion request to the OpenRouter API.
        
        Args:
            request: The chat completion request.
            
        Returns:
            Dict[str, Any]: The chat completion response.
            
        Raises:
            Exception: If the API request fails.
        """
        # Select the appropriate model based on the request
        model = self.select_model(request)
        
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content
                }
                for message in request.messages
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "n": request.n,
            "stream": False,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
        }
        
        # Add reasoning parameters if using a reasoning model
        if request.model == REASONING_MODEL_ID and model == OPENROUTER_REASONING_MODELS["high"]:
            payload["include_reasoning"] = request.include_reasoning
        
        # Send the request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            
            # Check for errors
            if response.status_code != 200:
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                raise Exception(f"{ERROR_OPENROUTER_API}: {error_detail}")
            
            # Parse the response
            result = response.json()
            
            # Extract the completion
            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            
            # Extract reasoning if available
            reasoning = None
            if request.include_reasoning and model == OPENROUTER_REASONING_MODELS["high"]:
                reasoning = message.get("reasoning")
            
            # Extract usage information
            usage = result.get("usage", {})
            
            # Get detailed cost information
            generation_id = result.get("id")
            cost_info = await self.get_generation_cost(generation_id)
            
            return {
                "content": content,
                "reasoning": reasoning,
                "model": result.get("model", model),
                "cost": cost_info["cost"],
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "model_id": cost_info.get("model"),
                    "provider": cost_info.get("provider"),
                    "generation_id": generation_id,
                    "generation_time": result.get("created", 0)
                }
            }
    
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a streaming chat completion request to the OpenRouter API.
        
        Args:
            request: The chat completion request.
            
        Yields:
            Dict[str, Any]: Chunks of the chat completion response.
            
        Raises:
            Exception: If the API request fails.
        """
        # Select the appropriate model based on the request
        model = self.select_model(request)
        
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content
                }
                for message in request.messages
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "n": request.n,
            "stream": True,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
        }
        
        # Add reasoning parameters if using a reasoning model
        if request.model == REASONING_MODEL_ID and model == OPENROUTER_REASONING_MODELS["high"]:
            payload["include_reasoning"] = request.include_reasoning
        
        # Initialize variables for tracking the response
        content_buffer = ""
        reasoning_buffer = ""
        generation_id = None
        model_name = model
        
        # Send the request
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60.0
            ) as response:
                # Check for errors
                if response.status_code != 200:
                    error_text = await response.text()
                    try:
                        error_json = json.loads(error_text)
                        error_detail = error_json.get("error", {}).get("message", "Unknown error")
                    except:
                        error_detail = error_text
                    raise Exception(f"{ERROR_OPENROUTER_API}: {error_detail}")
                
                # Process the streaming response
                async for line in response.aiter_lines():
                    # Skip empty lines
                    if not line.strip():
                        continue
                    
                    # Remove "data: " prefix
                    if line.startswith("data: "):
                        line = line[6:]
                    
                    # Check for end of stream
                    if line == "[DONE]":
                        break
                    
                    try:
                        # Parse the chunk
                        chunk = json.loads(line)
                        
                        # Extract the generation ID if not already set
                        if not generation_id:
                            generation_id = chunk.get("id")
                            model_name = chunk.get("model", model)
                        
                        # Extract the content delta
                        choice = chunk.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        content_delta = delta.get("content", "")
                        
                        # Extract reasoning delta if available
                        reasoning_delta = None
                        if request.include_reasoning and model == OPENROUTER_REASONING_MODELS["high"]:
                            reasoning_delta = delta.get("reasoning", "")
                            if reasoning_delta:
                                reasoning_buffer += reasoning_delta
                        
                        # Update the content buffer
                        if content_delta:
                            content_buffer += content_delta
                            
                            # Yield the content delta
                            yield {
                                "content": content_delta,
                                "reasoning": reasoning_delta,
                                "model": model_name,
                                "role": ROLE_ASSISTANT
                            }
                    except json.JSONDecodeError:
                        # Skip invalid JSON
                        continue
                
                # Get detailed cost information
                if generation_id:
                    try:
                        cost_info = await self.get_generation_cost(generation_id)
                        
                        # Yield the final chunk with cost information
                        yield {
                            "content": "",
                            "reasoning": "",
                            "model": model_name,
                            "is_final": True,
                            "finish_reason": "stop",
                            "cost": cost_info["cost"],
                            "usage": {
                                "prompt_tokens": cost_info["usage"].get("prompt_tokens", 0),
                                "completion_tokens": cost_info["usage"].get("completion_tokens", 0),
                                "total_tokens": cost_info["usage"].get("total_tokens", 0),
                                "model_id": cost_info.get("model"),
                                "provider": cost_info.get("provider"),
                                "generation_id": generation_id
                            }
                        }
                    except Exception as e:
                        # If we can't get cost information, yield a basic final chunk
                        yield {
                            "content": "",
                            "reasoning": "",
                            "model": model_name,
                            "is_final": True,
                            "finish_reason": "stop",
                            "cost": 0,
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": len(content_buffer) // 4,  # Rough estimate
                                "total_tokens": len(content_buffer) // 4,  # Rough estimate
                                "model_id": model_name,
                                "provider": "unknown",
                                "generation_id": generation_id
                            }
                        }
    
    def select_model(self, request: ChatRequest) -> str:
        """
        Select the appropriate model based on the request.
        
        Args:
            request: The chat completion request.
            
        Returns:
            str: The selected model identifier.
        """
        # If using the reasoning model, select based on reasoning effort
        if request.model == REASONING_MODEL_ID:
            # Default to medium reasoning effort if not specified
            effort = request.reasoning_effort or DEFAULT_REASONING_EFFORT
            
            # Validate reasoning effort
            if effort not in VALID_REASONING_EFFORTS:
                effort = DEFAULT_REASONING_EFFORT
            
            return OPENROUTER_REASONING_MODELS[effort]
        
        # Otherwise, use the specified model
        return OPENROUTER_GENERAL_MODEL