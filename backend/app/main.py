from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv, find_dotenv
from .api.tokens import router as tokens_router
import logging
import os

# Ensure .env is loaded when running the app module directly or via uvicorn
load_dotenv(find_dotenv())

# Configure basic logging so exceptions (like connection errors) are visible in the server logs
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
logger = logging.getLogger(__name__)
logger.info("Starting TokenTrust app (log level=%s)", log_level)

app = FastAPI(
    title="TokenTrust Agentic AI API",
    description="AI-powered token validation and risk assessment",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tokens_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "TokenTrust Agentic AI Risk Assessment API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "risk_agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)