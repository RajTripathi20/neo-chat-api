"""
Authentication service module.

This module provides functions for API key authentication, verification,
and management. It handles API key validation, user identification,
and API key lifecycle operations.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv
from datetime import datetime
from src.models.database import db
from src.utils.constants.auth import (
    AUTH_HEADER, BEARER_PREFIX, DEMO_API_KEY, DEMO_USER_ID, DEMO_PLAN
)
from src.utils.constants.errors import (
    ERROR_MISSING_API_KEY, ERROR_INVALID_API_KEY
)
from src.utils.constants.http import HTTP_UNAUTHORIZED

# Load environment variables
load_dotenv()

# API key header
API_KEY_HEADER = APIKeyHeader(name=AUTH_HEADER, auto_error=False)

async def verify_api_key(
    request: Request,
    api_key: str = Depends(API_KEY_HEADER)
) -> str:
    """
    Verify the API key and return the user ID if valid.
    
    Args:
        request: The FastAPI request object.
        api_key: The API key from the Authorization header.
        
    Returns:
        str: The API key if valid.
        
    Raises:
        HTTPException: If the API key is missing or invalid.
    """
    if not api_key:
        raise HTTPException(
            status_code=HTTP_UNAUTHORIZED,
            detail=ERROR_MISSING_API_KEY,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Remove 'Bearer ' prefix if present
    if api_key.startswith(BEARER_PREFIX):
        api_key = api_key[len(BEARER_PREFIX):]
    
    # Check if API key exists in database
    query = """
    SELECT a.key, a.user_id, u.balance
    FROM api_keys a
    JOIN users u ON a.user_id = u.id
    WHERE a.key = $1
    """
    result = await db.fetchrow(query, api_key)
    
    if not result:
        raise HTTPException(
            status_code=HTTP_UNAUTHORIZED,
            detail=ERROR_INVALID_API_KEY,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last used timestamp
    update_query = """
    UPDATE api_keys
    SET last_used_at = $1
    WHERE key = $2
    """
    await db.execute(update_query, datetime.utcnow(), api_key)
    
    # Store user info in request state
    request.state.user_id = result["user_id"]
    request.state.balance = result["balance"]
    
    return api_key

def get_user_id(request: Request) -> str:
    """
    Get the user ID from the request state.
    
    Args:
        request: The FastAPI request object.
        
    Returns:
        str: The user ID.
    """
    return getattr(request.state, "user_id", "anonymous")

def get_user_balance(request: Request) -> float:
    """
    Get the user balance from the request state.
    
    Args:
        request: The FastAPI request object.
        
    Returns:
        float: The user balance.
    """
    return getattr(request.state, "balance", 0.0)

async def create_api_key(user_id: str, name: str) -> str:
    """
    Create a new API key for a user.
    
    Args:
        user_id: The ID of the user.
        name: A name for the API key.
        
    Returns:
        str: The newly created API key.
    """
    # Generate a new API key
    import uuid
    api_key = f"sk-neochat-{uuid.uuid4()}"
    
    # Insert into database
    query = """
    INSERT INTO api_keys (key, user_id, name, created_at, last_used_at)
    VALUES ($1, $2, $3, $4, $4)
    """
    await db.execute(query, api_key, user_id, name, datetime.utcnow())
    
    return api_key

async def list_api_keys(user_id: str):
    """
    List all API keys for a user.
    
    Args:
        user_id: The ID of the user.
        
    Returns:
        list: A list of API keys.
    """
    query = """
    SELECT key, name, created_at, last_used_at
    FROM api_keys
    WHERE user_id = $1
    ORDER BY created_at DESC
    """
    return await db.fetch(query, user_id)

async def delete_api_key(user_id: str, api_key: str) -> bool:
    """
    Delete an API key.
    
    Args:
        user_id: The ID of the user.
        api_key: The API key to delete.
        
    Returns:
        bool: True if the API key was deleted, False otherwise.
    """
    query = """
    DELETE FROM api_keys
    WHERE key = $1 AND user_id = $2
    """
    result = await db.execute(query, api_key, user_id)
    return result and result > 0 