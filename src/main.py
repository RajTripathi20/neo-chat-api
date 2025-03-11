import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.utils.constants.api import (
    API_TITLE, 
    API_DESCRIPTION, 
    API_VERSION_NUMBER,
    API_PREFIX, 
    HEALTH_CHECK_PATH
)
from src.utils.constants.server import (
    DEFAULT_HOST, 
    DEFAULT_PORT,
    DEBUG_ENV_VAR
)
from src.utils.constants.http import HEADER_PROCESS_TIME

# Load environment variables
load_dotenv()

# Import routers
from src.api.openai_compat import router as openai_router

# Import middleware
from src.api.middleware import AuthMiddleware, RateLimitMiddleware, CreditCheckMiddleware
from src.utils.logging import RequestLoggingMiddleware, log_info, log_error

"""
Main application module.

This module initializes the FastAPI application, sets up middleware,
registers routers, and defines startup and shutdown events.
"""

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION_NUMBER,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CreditCheckMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add routers
app.include_router(openai_router, prefix=API_PREFIX)

# Health check endpoint
@app.get(HEALTH_CHECK_PATH)
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        dict: A dictionary containing the status and version of the API.
    """
    return {"status": "ok", "version": API_VERSION_NUMBER}

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware to add a header with the processing time of the request.
    
    Args:
        request: The incoming request.
        call_next: The next middleware or route handler.
        
    Returns:
        Response: The response with the X-Process-Time header added.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers[HEADER_PROCESS_TIME] = str(process_time)
    return response

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs when the application starts.
    
    Initializes the database connection and runs migrations.
    """
    # Initialize database connection
    from src.models.database import db
    try:
        await db.connect()
        log_info("Connected to database")
        
        # Run database migrations
        from src.models.migrations import run_migrations
        await run_migrations()
        log_info("Database migrations completed")
    except Exception as e:
        log_error(f"Failed to initialize database: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Event handler that runs when the application shuts down.
    
    Closes the database connection.
    """
    # Close database connection
    from src.models.database import db
    try:
        await db.disconnect()
        log_info("Disconnected from database")
    except Exception as e:
        log_error(f"Failed to disconnect from database: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=os.getenv("HOST", DEFAULT_HOST),
        port=int(os.getenv("PORT", DEFAULT_PORT)),
        reload=os.getenv(DEBUG_ENV_VAR, "False").lower() == "true",
    ) 