"""
Logging configuration module.

This module provides logging functionality for the application,
including request/response logging, error logging, and usage tracking.
"""

import logging
import os
import json
import time
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Any, Optional
from src.utils.constants.http import HEADER_PROCESS_TIME, HEADER_REQUEST_ID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log"),
    ]
)

# Create logger
logger = logging.getLogger("neo-chat")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses.
    
    This middleware logs information about incoming requests and outgoing
    responses, including timing information and error details.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and log information about it.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.
            
        Returns:
            Response: The response from the next middleware or route handler.
        """
        # Generate request ID
        request_id = request.headers.get(HEADER_REQUEST_ID, f"req-{time.time()}")
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add processing time header
            response.headers[HEADER_PROCESS_TIME] = str(process_time)
            
            # Log response
            await self._log_response(request, response, request_id, process_time)
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            await self._log_error(request, e, request_id, process_time)
            
            # Re-raise the exception
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """
        Log information about an incoming request.
        
        Args:
            request: The incoming request.
            request_id: The unique identifier for the request.
        """
        # Get request details
        client_host = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", "anonymous")
        
        # Log request
        log_info(
            f"Request {request_id}: {request.method} {request.url.path}",
            {
                "request_id": request_id,
                "client_ip": client_host,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
            }
        )
    
    async def _log_response(self, request: Request, response: Response, request_id: str, process_time: float):
        """
        Log information about an outgoing response.
        
        Args:
            request: The incoming request.
            response: The outgoing response.
            request_id: The unique identifier for the request.
            process_time: The time taken to process the request.
        """
        log_info(
            f"Response {request_id}: {response.status_code} in {process_time:.4f}s",
            {
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time,
            }
        )
    
    async def _log_error(self, request: Request, exception: Exception, request_id: str, process_time: float):
        """
        Log information about an error that occurred during request processing.
        
        Args:
            request: The incoming request.
            exception: The exception that occurred.
            request_id: The unique identifier for the request.
            process_time: The time taken before the error occurred.
        """
        log_error(
            f"Error {request_id}: {str(exception)} in {process_time:.4f}s",
            {
                "request_id": request_id,
                "error": str(exception),
                "error_type": type(exception).__name__,
                "process_time": process_time,
            }
        )

def log_info(message: str, extra: Optional[Dict[str, Any]] = None):
    """
    Log an informational message.
    
    Args:
        message: The message to log.
        extra: Additional information to include in the log.
    """
    logger.info(message, extra=extra or {})

def log_error(message: str, extra: Optional[Dict[str, Any]] = None):
    """
    Log an error message.
    
    Args:
        message: The message to log.
        extra: Additional information to include in the log.
    """
    logger.error(message, extra=extra or {})

def log_warning(message: str, extra: Optional[Dict[str, Any]] = None):
    """
    Log a warning message.
    
    Args:
        message: The message to log.
        extra: Additional information to include in the log.
    """
    logger.warning(message, extra=extra or {})

def log_debug(message: str, extra: Optional[Dict[str, Any]] = None):
    """
    Log a debug message.
    
    Args:
        message: The message to log.
        extra: Additional information to include in the log.
    """
    logger.debug(message, extra=extra or {})

def log_usage(user_id: str, request_id: str, model: str, tokens: Dict[str, int], cost: float):
    """
    Log usage information for billing and analytics.
    
    Args:
        user_id: The ID of the user.
        request_id: The unique identifier for the request.
        model: The model used for the request.
        tokens: Token usage information.
        cost: The cost of the request.
    """
    log_info(
        f"Usage: {user_id} used {model} for {tokens.get('total', 0)} tokens (${cost:.6f})",
        {
            "type": "usage",
            "user_id": user_id,
            "request_id": request_id,
            "model": model,
            "tokens": tokens,
            "cost": cost,
            "timestamp": datetime.utcnow().isoformat(),
        }
    ) 