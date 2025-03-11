"""
Rate limiting service module.

This module provides functionality for rate limiting API requests
to prevent abuse and ensure fair usage of the API.
"""

from fastapi import HTTPException, Request, status
import time
import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.models.database import db
from src.services.authentication import get_user_id
from src.utils.constants.api import DEFAULT_RATE_LIMIT, DEFAULT_BURST_LIMIT
from src.utils.constants.errors import ERROR_RATE_LIMIT_EXCEEDED
from src.utils.constants.http import HTTP_TOO_MANY_REQUESTS

# Load environment variables
load_dotenv()

# Rate limit configurations
rate_limits = {
    "default": {"limit": DEFAULT_RATE_LIMIT, "window": 3600},  # requests per hour
    "high_volume": {"limit": 5000, "window": 60}  # requests per minute
}

class RateLimiter:
    """
    Rate limiter class for controlling API request rates.
    
    This class provides methods to check and enforce rate limits
    based on API keys and user plans.
    """
    
    def __init__(self):
        """
        Initialize the rate limiter.
        """
        pass
    
    async def check_rate_limit(self, api_key: str, request: Request = None):
        """
        Check if the request exceeds the rate limit.
        
        Args:
            api_key: The API key to check.
            request: The FastAPI request object (optional).
            
        Raises:
            HTTPException: If the rate limit is exceeded.
        """
        # Get user ID
        if request:
            user_id = get_user_id(request)
        else:
            # If no request object, use API key as user ID
            user_id = api_key
        
        # Get endpoint
        endpoint = request.url.path if request else "unknown"
        
        # Get rate limit configuration
        # In a real implementation, this would be based on the user's plan
        limit_config = rate_limits.get("default")
        limit = limit_config["limit"]
        window = limit_config["window"]
        
        # Get current timestamp
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=window)
        
        # Create a unique ID for this rate limit window
        rate_limit_id = f"{user_id}:{endpoint}:{int(current_time.timestamp()) // window}"
        
        # Check if rate limit exists
        query = """
        SELECT count FROM rate_limits
        WHERE id = $1
        """
        count = await db.fetchval(query, rate_limit_id)
        
        if count is None:
            # Create new rate limit entry
            insert_query = """
            INSERT INTO rate_limits (id, user_id, endpoint, count, window_start)
            VALUES ($1, $2, $3, 1, $4)
            """
            await db.execute(insert_query, rate_limit_id, user_id, endpoint, current_time)
            count = 1
        else:
            # Increment count
            update_query = """
            UPDATE rate_limits
            SET count = count + 1
            WHERE id = $1
            """
            await db.execute(update_query, rate_limit_id)
            count += 1
        
        # Clean up old entries
        await self._cleanup_old_entries(window_start)
        
        # Check if rate limit exceeded
        if count > limit:
            raise HTTPException(
                status_code=HTTP_TOO_MANY_REQUESTS,
                detail=ERROR_RATE_LIMIT_EXCEEDED,
            )
    
    async def _cleanup_old_entries(self, window_start):
        """
        Clean up old rate limit entries.
        
        Args:
            window_start: The start of the current rate limit window.
        """
        # Delete entries older than window_start
        query = """
        DELETE FROM rate_limits
        WHERE window_start < $1
        """
        await db.execute(query, window_start)

# Create a singleton instance
rate_limiter = RateLimiter()

async def check_rate_limit(api_key: str, request: Request = None):
    """
    Check if the request exceeds the rate limit.
    
    This is a convenience function that delegates to the RateLimiter class.
    
    Args:
        api_key: The API key to check.
        request: The FastAPI request object (optional).
        
    Raises:
        HTTPException: If the rate limit is exceeded.
    """
    await rate_limiter.check_rate_limit(api_key, request) 