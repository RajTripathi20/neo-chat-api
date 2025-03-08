from fastapi import Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API key header
API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)

# In a real implementation, this would be replaced with a database lookup
# For now, we'll use a simple in-memory dictionary for demonstration
API_KEYS = {
    "sk-neochat-demo": {
        "user_id": "demo-user",
        "plan": "free"
    }
}

async def verify_api_key(
    request: Request,
    api_key: str = Depends(API_KEY_HEADER)
) -> str:
    """
    Verify the API key and return the user ID if valid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Remove 'Bearer ' prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    # Check if API key exists
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Store user info in request state for later use
    request.state.user_id = API_KEYS[api_key]["user_id"]
    request.state.plan = API_KEYS[api_key]["plan"]
    
    return api_key

def get_user_plan(request: Request) -> str:
    """
    Get the user's plan from the request state
    """
    return getattr(request.state, "plan", "free")

def get_user_id(request: Request) -> str:
    """
    Get the user ID from the request state
    """
    return getattr(request.state, "user_id", "anonymous") 