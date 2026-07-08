"""
FastAPI application entrypoint for Nepali Finance Analyzer.
"""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import db module — handle both direct run and package import
try:
    from db import init_db
    from routers import analytics, chat, sample, transactions, upload
except ImportError:
    from backend.db import init_db
    from backend.routers import analytics, chat, sample, transactions, upload

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nepali Finance Analyzer API",
    description="Personal finance analysis tool for Nepali bank users",
    version="1.0.0",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Register all routers under the /api prefix
# ------------------------------------------------------------------
app.include_router(upload.router, prefix="/api")
app.include_router(sample.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Nepali Finance Analyzer API"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    # Warn if GROQ_API_KEY is missing but let the server start so it can be
    # tested without a real API key (endpoints that need it will fail gracefully).
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        logger.warning(
            "GROQ_API_KEY is not set. Endpoints that call the Groq API "
            "(upload, analytics, chat) will return errors until the key is provided. "
            "Get a free key at https://console.groq.com"
        )

    # Initialize SQLite database and create transactions table
    init_db()
    logger.info("Database initialized successfully")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
