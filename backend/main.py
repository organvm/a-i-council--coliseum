"""
FastAPI Main Application.

Main entry point for the AI Council Coliseum backend.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

try:
    from backend.api import (
        achievements_router,
        agents_router,
        blockchain_router,
        events_router,
        users_router,
        voting_router,
    )
    from backend.api.dependencies import get_orchestrator, initialize_orchestrator
    from backend.database import engine, Base
    from backend.event_pipeline.worker import AutonomousArenaWorker
except ImportError:
    # Supports running from backend/ as module path main:app
    from api import (
        achievements_router,
        agents_router,
        blockchain_router,
        events_router,
        users_router,
        voting_router,
    )
    from api.dependencies import get_orchestrator, initialize_orchestrator
    from database import engine, Base
    from event_pipeline.worker import AutonomousArenaWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Handle stale connections
                pass


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application."""
    logger.info("Starting AI Council Coliseum Backend")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await initialize_orchestrator()
    orchestrator = get_orchestrator()
    
    # Inject broadcast capability into orchestrator
    async def socket_broadcast(event_type: str, data: dict):
        await manager.broadcast({"type": event_type, "data": data})
    
    # Override broadcast methods to also send to websockets
    original_broadcast = orchestrator.broadcast_message
    async def enhanced_broadcast(message):
        await original_broadcast(message)
        await socket_broadcast("agent_message", message.model_dump())
    
    orchestrator.broadcast_message = enhanced_broadcast
    
    await orchestrator.start()

    # Start Autonomous Worker
    arena_worker = AutonomousArenaWorker(orchestrator, interval_seconds=120)
    await arena_worker.start()

    yield

    logger.info("Shutting down AI Council Coliseum Backend")
    await arena_worker.stop()
    await orchestrator.stop()


app = FastAPI(
    title="AI Council Coliseum",
    description=(
        "A decentralized 24/7 live streaming platform where AI agents debate real-time events"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(events_router, prefix="/api/events", tags=["events"])
app.include_router(voting_router, prefix="/api/voting", tags=["voting"])
app.include_router(blockchain_router, prefix="/api/blockchain", tags=["blockchain"])
app.include_router(achievements_router, prefix="/api/achievements", tags=["achievements"])
app.include_router(users_router, prefix="/api/users", tags=["users"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to AI Council Coliseum API",
        "version": "1.0.0",
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-council-coliseum"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket disconnected")


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
