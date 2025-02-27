from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Import our API routers
from nba_api.api.endpoints.players import router as players_router
from nba_api.api.endpoints.calendar import router as calendar_router
from nba_api.api.endpoints.stats import router as stats_router
from nba_api.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Check for API key
if not os.environ.get("BALLDONTLIE_API_KEY"):
    logger.warning("BALLDONTLIE_API_KEY environment variable not set")
    logger.warning("API calls may fail. Please set this variable before running the server.")

# Create the FastAPI application
app = FastAPI(
    title="NBA Player Analysis API",
    description="API for analyzing NBA player performance and game schedules",
    version="0.1.0",
)

# Add CORS middleware to allow cross-origin requests (useful for web frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory rate limiting
request_counts = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware."""
    client_ip = request.client.host
    
    # Simple in-memory rate limiting (could be replaced with Redis in production)
    if client_ip in request_counts:
        if request_counts[client_ip]["count"] > 100 and \
           time.time() - request_counts[client_ip]["timestamp"] < 60:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"message": "Too many requests. Please try again later."}
            )
        request_counts[client_ip]["count"] += 1
    else:
        request_counts[client_ip] = {"count": 1, "timestamp": time.time()}
    
    response = await call_next(request)
    return response

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    path = request.url.path
    query_params = str(request.query_params)
    
    logger.info(f"Request start: {request.method} {path} {query_params}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Request completed: {request.method} {path} {response.status_code} ({process_time:.3f}s)")
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions globally."""
    # Log the error
    logger.exception(f"Unhandled exception on {request.url}: {str(exc)}")
    
    # Return a user-friendly response
    return JSONResponse(
        status_code=500,
        content={
            "message": "An unexpected error occurred",
            "error_type": type(exc).__name__,
            # Only include detailed error info in development
            "detail": str(exc) if os.getenv("ENVIRONMENT") == "development" else None
        }
    )

# Include our routers
app.include_router(players_router)
app.include_router(calendar_router)
app.include_router(stats_router)

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint with basic information."""
    return {
        "message": "Welcome to the NBA Player Analysis API",
        "docs_url": "/docs",
        "version": "0.1.0",
    }

# Run the application if this file is executed directly
if __name__ == "__main__":
    logger.info("Starting NBA Player Analysis API")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)