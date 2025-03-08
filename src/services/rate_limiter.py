from fastapi import HTTPException, Request, status
import time
import os
from dotenv import load_dotenv
from src.services.authentication import get_user_plan, get_user_id

# Load environment variables
load_dotenv()

# In a real implementation, this would use Redis or another distributed cache
# For now, we'll use a simple in-memory dictionary for demonstration
rate_limits = {
    "free": {"limit": 100, "window": 3600},  # 100 requests per hour
    "pro": {"limit": 5000, "window": 60}     # 5000 requests per minute
}

# In-memory storage for request counts
request_counts = {}

class RateLimiter:
    def __init__(self):
        self.request_counts = {}
    
    async def check_rate_limit(self, api_key: str, request: Request = None):
        """
        Check if the request exceeds the rate limit
        """
        # Get user plan
        if request:
            plan = get_user_plan(request)
            user_id = get_user_id(request)
        else:
            # Default to free plan if request object not available
            plan = "free"
            user_id = api_key
        
        # Get rate limit for the plan
        limit_config = rate_limits.get(plan, rate_limits["free"])
        limit = limit_config["limit"]
        window = limit_config["window"]
        
        # Get current timestamp
        current_time = int(time.time())
        
        # Create key for the user
        key = f"{user_id}:{current_time // window}"
        
        # Get current count
        if key not in self.request_counts:
            self.request_counts[key] = 0
        
        # Check if limit exceeded
        if self.request_counts[key] >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {window - (current_time % window)} seconds.",
                headers={"Retry-After": str(window - (current_time % window))},
            )
        
        # Increment count
        self.request_counts[key] += 1
        
        # Clean up old entries (simple garbage collection)
        if len(self.request_counts) > 1000:
            self._cleanup_old_entries(current_time, window)
    
    def _cleanup_old_entries(self, current_time, window):
        """
        Remove old entries from the request counts dictionary
        """
        current_window = current_time // window
        keys_to_remove = [k for k in self.request_counts.keys() if int(k.split(":")[-1]) < current_window]
        for key in keys_to_remove:
            del self.request_counts[key]

# Create a singleton instance
rate_limiter = RateLimiter()

# Function to check rate limit
async def check_rate_limit(api_key: str, request: Request = None):
    """
    Check if the request exceeds the rate limit
    """
    await rate_limiter.check_rate_limit(api_key, request) 