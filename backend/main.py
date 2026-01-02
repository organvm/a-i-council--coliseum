"""
FastAPI Main Application

Main entry point for the AI Council Coliseum backend.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from .api import (
    agents_router,
    events_router,
    voting_router,
    blockchain_router,
    achievements_router,
    users_router
)
from .api.dependencies import initialize_orchestrator, get_orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application"""
    # Startup
    logger.info("🚀 Starting AI Council Coliseum Backend...")
    await initialize_orchestrator()
    yield
    # Shutdown
    logger.info("👋 Shutting down AI Council Coliseum Backend...")
    orchestrator = get_orchestrator()
    await orchestrator.stop()


app = FastAPI(
    title="AI Council Coliseum",
    description="A decentralized 24/7 live streaming platform where AI agents debate real-time events",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(events_router, prefix="/api/events", tags=["events"])
app.include_router(voting_router, prefix="/api/voting", tags=["voting"])
app.include_router(blockchain_router, prefix="/api/blockchain", tags=["blockchain"])
app.include_router(achievements_router, prefix="/api/achievements", tags=["achievements"])
app.include_router(users_router, prefix="/api/users", tags=["users"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to AI Council Coliseum API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-council-coliseum"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print("WebSocket disconnected")


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
