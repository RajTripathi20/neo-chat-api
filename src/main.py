import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from src.api.openai_compat import router as openai_router

# Import middleware
from src.api.middleware import AuthMiddleware, RateLimitMiddleware, CreditCheckMiddleware

# Create FastAPI app
app = FastAPI(
    title="Neo-Chat AI Orchestration Layer",
    description="OpenAI-compatible API with enterprise features",
    version="0.1.0",
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

# Add routers
app.include_router(openai_router, prefix="/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Startup event
@app.on_event("startup")
async def startup_event():
    # Initialize database connection
    from src.models.database import db
    try:
        await db.connect()
        print("Connected to database")
    except Exception as e:
        print(f"Failed to connect to database: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    # Close database connection
    from src.models.database import db
    try:
        await db.disconnect()
        print("Disconnected from database")
    except Exception as e:
        print(f"Failed to disconnect from database: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true",
    ) 