"""
FastAPI Main Application.

Main entry point for the AI Council Coliseum backend.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

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
    from backend.social.twitch_listener import TwitchListener
    from backend.infrastructure.event_bus import event_bus
    from backend.event_pipeline.ingestion import EventSource
    from backend.settings import get_settings
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
    from social.twitch_listener import TwitchListener
    from infrastructure.event_bus import event_bus
    from event_pipeline.ingestion import EventSource
    from settings import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket connected (active_connections=%s)",
            len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                "WebSocket disconnected (active_connections=%s)",
                len(self.active_connections),
            )

    async def broadcast(self, message: dict[str, Any]):
        failed_connections: list[WebSocket] = []
        for connection in self.active_connections[:]:
            try:
                await connection.send_json(message)
            except Exception:
                failed_connections.append(connection)
                logger.warning("WebSocket broadcast failed; pruning connection", exc_info=True)

        for connection in failed_connections:
            self.disconnect(connection)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application."""
    logger.info("Lifespan startup begin")

    orchestrator = None
    arena_worker: AutonomousArenaWorker | None = None
    twitch_listener: TwitchListener | None = None
    subscribed_ws_forwarder = False

    async def stop_component(name: str, stop_callable):
        try:
            await stop_callable()
        except Exception:
            logger.exception("Failed to stop component: %s", name)

    # Pass EventBus messages to WebSocket clients
    async def ws_forwarder(event_type: str, data: dict | None):
        payload_data = data or {}
        try:
            await manager.broadcast({"type": event_type, "data": payload_data})
        except Exception:
            logger.exception("Failed forwarding event_bus message to websockets (event_type=%s)", event_type)

    try:
        logger.info("Startup step: create database tables")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Startup step: initialize orchestrator")
        await initialize_orchestrator()
        orchestrator = get_orchestrator()

        logger.info("Startup step: start event bus")
        await event_bus.start()

        event_bus.subscribe("*", ws_forwarder)
        subscribed_ws_forwarder = True

        logger.info("Startup step: start orchestrator")
        await orchestrator.start()

        logger.info("Startup step: start arena worker")
        arena_worker = AutonomousArenaWorker(orchestrator, interval_seconds=15)
        await arena_worker.start()

        # Twitch Handler
        async def handle_twitch_message(user: str, message: str):
            try:
                # Broadcast chat to frontend for overlay
                await event_bus.publish("chat_message", {"user": user, "message": message})

                # Ingest social event into the main pipeline instead of inline command parsing
                await orchestrator.ingest_event(
                    source=EventSource.SOCIAL_MEDIA,
                    raw_data={
                        "title": f"Twitch chat from {user}",
                        "description": message,
                        "user": user,
                    },
                    metadata={"platform": "twitch"},
                )
            except Exception:
                logger.exception("Failed handling Twitch message (user=%s)", user)
                raise

        logger.info("Startup step: start twitch listener")
        twitch_listener = TwitchListener(callback=handle_twitch_message)
        await twitch_listener.start()

        logger.info("Lifespan startup complete")
        yield
    except Exception:
        logger.exception("Lifespan startup/runtime failure")
        raise
    finally:
        logger.info("Lifespan shutdown begin")
        if subscribed_ws_forwarder:
            try:
                event_bus.unsubscribe("*", ws_forwarder)
            except Exception:
                logger.exception("Failed to unsubscribe websocket forwarder")

        if twitch_listener is not None:
            await stop_component("twitch_listener", twitch_listener.stop)

        if arena_worker is not None:
            await stop_component("arena_worker", arena_worker.stop)

        if orchestrator is not None:
            await stop_component("orchestrator", orchestrator.stop)

        await stop_component("event_bus", event_bus.stop)
        logger.info("Lifespan shutdown complete")


app = FastAPI(
    title="AI Council Coliseum",
    description=(
        "A decentralized 24/7 live streaming platform where AI agents debate with viewer crypto participation"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

origins = get_settings().cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware:
    """Pure ASGI middleware to add security headers."""
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"x-content-type-options"] = b"nosniff"
                headers[b"x-frame-options"] = b"DENY"
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                message["headers"] = list(headers.items())
            await send(message)

        await self.app(scope, receive, send_wrapper)


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
        logger.info("WebSocket client closed connection")
    except Exception:
        logger.exception("WebSocket endpoint error")
    finally:
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
