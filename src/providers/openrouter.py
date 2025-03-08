import os
import json
import httpx
from typing import Dict, Any, List
from dotenv import load_dotenv
from src.models.api_models import ChatRequest

# Load environment variables
load_dotenv()

class RouterClient:
    """Client for OpenRouter API"""
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://neo-chat.in",  # Replace with your actual domain
            "X-Title": "Neo-Chat AI"
        }
    
    async def chat(self, request: ChatRequest) -> Dict[str, Any]:
        """
        Send a chat request to OpenRouter
        """
        # Select the appropriate model based on the request
        model = self.select_model(request)
        
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": [m.dict() for m in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "n": request.n,
            "stream": False,  # We handle streaming separately
            "user": request.user
        }
        
        # Add stop sequences if provided
        if request.stop:
            payload["stop"] = request.stop
        
        # Add presence and frequency penalties if provided
        if request.presence_penalty:
            payload["presence_penalty"] = request.presence_penalty
        if request.frequency_penalty:
            payload["frequency_penalty"] = request.frequency_penalty
        
        # Send the request to OpenRouter
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60.0  # Longer timeout for LLM responses
            )
            
            # Check for errors
            if response.status_code != 200:
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                raise Exception(f"OpenRouter API error: {error_detail}")
            
            # Parse the response
            result = response.json()
            
            # Extract the relevant information
            return {
                "content": result["choices"][0]["message"]["content"],
                "model": result["model"],
                "cost": result.get("usage", {}).get("cost", 0.0),
                "usage": {
                    "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": result.get("usage", {}).get("total_tokens", 0)
                }
            }
    
    def select_model(self, request: ChatRequest) -> str:
        """
        Select the appropriate model based on the request content
        """
        # If the user specified a model, use that
        if request.model and request.model != "auto":
            return request.model
        
        # Check if the request contains code
        contains_code = any("```" in m.content for m in request.messages if hasattr(m, "content"))
        
        # Select model based on content
        if contains_code:
            return "qwen/qwen-2.5-coder-32b-instruct:free"
        
        # Default to a general-purpose model
        return "meta-llama/llama-3.3-70b-instruct:free" 