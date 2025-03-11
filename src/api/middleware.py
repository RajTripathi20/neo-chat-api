import time
import asyncio
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.services.authentication import verify_api_key
from src.services.rate_limiter import check_rate_limit
from src.services.accounting import credit_manager
from src.utils.constants.api import API_PREFIX, CHAT_COMPLETIONS_PATH
from src.utils.constants.auth import AUTH_HEADER, BEARER_PREFIX, DEMO_API_KEY, DEMO_USER_ID, DEMO_PLAN
from src.utils.constants.errors import ERROR_MISSING_API_KEY, ERROR_INVALID_API_KEY, ERROR_INSUFFICIENT_CREDITS
from src.utils.constants.http import HTTP_UNAUTHORIZED, HTTP_PAYMENT_REQUIRED, HTTP_TOO_MANY_REQUESTS, HTTP_INTERNAL_SERVER_ERROR

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.
    
    This middleware verifies that requests to API endpoints include a valid API key.
    It skips authentication for non-API routes.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for non-API routes
        if not request.url.path.startswith(API_PREFIX):
            return await call_next(request)
        
        # Get API key from header
        auth_header = request.headers.get(AUTH_HEADER)
        if not auth_header:
            return Response(
                content=f'{{"error": "{ERROR_MISSING_API_KEY}"}}',
                status_code=HTTP_UNAUTHORIZED,
                media_type="application/json"
            )
        
        # Remove 'Bearer ' prefix if present
        if auth_header.startswith(BEARER_PREFIX):
            auth_header = auth_header[len(BEARER_PREFIX):]
        
        try:
            # Verify API key
            # In a real implementation, this would check against the database
            # For now, we'll use a simple in-memory check
            if auth_header != DEMO_API_KEY:
                return Response(
                    content=f'{{"error": "{ERROR_INVALID_API_KEY}"}}',
                    status_code=HTTP_UNAUTHORIZED,
                    media_type="application/json"
                )
            
            # Store user info in request state
            request.state.user_id = DEMO_USER_ID
            request.state.plan = DEMO_PLAN
            
            # Continue with the request
            return await call_next(request)
        except Exception as e:
            return Response(
                content=f'{{"error": "{str(e)}"}}',
                status_code=HTTP_INTERNAL_SERVER_ERROR,
                media_type="application/json"
            )

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting.
    
    This middleware enforces rate limits on API requests based on the API key.
    It skips rate limiting for non-API routes.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for non-API routes
        if not request.url.path.startswith(API_PREFIX):
            return await call_next(request)
        
        # Get API key from header
        auth_header = request.headers.get(AUTH_HEADER)
        if not auth_header:
            return await call_next(request)
        
        # Remove 'Bearer ' prefix if present
        if auth_header.startswith(BEARER_PREFIX):
            auth_header = auth_header[len(BEARER_PREFIX):]
        
        try:
            # Check rate limit
            await check_rate_limit(auth_header, request)
            
            # Continue with the request
            return await call_next(request)
        except Exception as e:
            return Response(
                content=f'{{"error": "{str(e)}"}}',
                status_code=HTTP_TOO_MANY_REQUESTS,
                media_type="application/json"
            )

class CreditCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware for credit checking.
    
    This middleware verifies that the user has sufficient credits to make API requests.
    It only checks credits for chat completion requests.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip credit checking for non-chat completion routes
        if not request.url.path.startswith(f"{API_PREFIX}{CHAT_COMPLETIONS_PATH}"):
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
                    content=f'{{"error": "{ERROR_INSUFFICIENT_CREDITS}"}}',
                    status_code=HTTP_PAYMENT_REQUIRED,
                    media_type="application/json"
                )
            
            # Continue with the request
            return await call_next(request)
        except Exception as e:
            return Response(
                content=f'{{"error": "{str(e)}"}}',
                status_code=HTTP_INTERNAL_SERVER_ERROR,
                media_type="application/json"
            ) 