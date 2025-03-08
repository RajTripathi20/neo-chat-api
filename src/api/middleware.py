import time
import asyncio
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.services.authentication import verify_api_key
from src.services.rate_limiter import check_rate_limit
from src.services.accounting import credit_manager

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for non-API routes
        if not request.url.path.startswith("/v1"):
            return await call_next(request)
        
        # Get API key from header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return Response(
                content='{"error": "Missing API key"}',
                status_code=401,
                media_type="application/json"
            )
        
        # Remove 'Bearer ' prefix if present
        if auth_header.startswith("Bearer "):
            auth_header = auth_header[7:]
        
        try:
            # Verify API key
            # In a real implementation, this would check against the database
            # For now, we'll use a simple in-memory check
            if auth_header != "sk-neochat-demo":
                return Response(
                    content='{"error": "Invalid API key"}',
                    status_code=401,
                    media_type="application/json"
                )
            
            # Store user info in request state
            request.state.user_id = "demo-user"
            request.state.plan = "free"
            
            # Continue with the request
            return await call_next(request)
        except Exception as e:
            return Response(
                content=f'{{"error": "{str(e)}"}}',
                status_code=500,
                media_type="application/json"
            )

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for non-API routes
        if not request.url.path.startswith("/v1"):
            return await call_next(request)
        
        # Get API key from header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return await call_next(request)
        
        # Remove 'Bearer ' prefix if present
        if auth_header.startswith("Bearer "):
            auth_header = auth_header[7:]
        
        try:
            # Check rate limit
            await check_rate_limit(auth_header, request)
            
            # Continue with the request
            return await call_next(request)
        except Exception as e:
            return Response(
                content=f'{{"error": "{str(e)}"}}',
                status_code=429,
                media_type="application/json"
            )

class CreditCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for credit checking"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip credit checking for non-API routes
        if not request.url.path.startswith("/v1/chat/completions"):
            return await call_next(request)
        
        # Get user ID from request state
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            return await call_next(request)
        
        try:
            # Check if user has sufficient credits
            # In a real implementation, this would check the actual cost
            # For now, we'll use a fixed cost for demonstration
            balance = await credit_manager.get_balance(user_id)
            if balance <= 0:
                return Response(
                    content='{"error": "Insufficient credits"}',
                    status_code=402,
                    media_type="application/json"
                )
            
            # Continue with the request
            return await call_next(request)
        except Exception as e:
            return Response(
                content=f'{{"error": "{str(e)}"}}',
                status_code=500,
                media_type="application/json"
            ) 