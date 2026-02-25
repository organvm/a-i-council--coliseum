"""
FastAPI Main Application.

Main entry point for the AI Council Coliseum backend.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

try:
    from backend.api import (
        achievements_router,
        agents_router,
        blockchain_router,
        demo_router,
        events_router,
        state_router,
        users_router,
        voting_router,
    )
    from backend.api.dependencies import get_orchestrator, initialize_orchestrator
    from backend.database import engine, Base
    from backend.demo import DemoDirector
    from backend.event_pipeline.worker import AutonomousArenaWorker
    from backend.social.twitch_listener import TwitchListener
    from backend.infrastructure.event_bus import event_bus
    from backend.event_pipeline.ingestion import EventSource
    from backend.settings import get_settings
    from sqlalchemy import text
except ImportError:
    # Supports running from backend/ as module path main:app
    from api import (
        achievements_router,
        agents_router,
        blockchain_router,
        demo_router,
        events_router,
        state_router,
        users_router,
        voting_router,
    )
    from api.dependencies import get_orchestrator, initialize_orchestrator
    from database import engine, Base
    from demo import DemoDirector
    from event_pipeline.worker import AutonomousArenaWorker
    from social.twitch_listener import TwitchListener
    from infrastructure.event_bus import event_bus
    from event_pipeline.ingestion import EventSource
    from settings import get_settings
    from sqlalchemy import text

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
                await connection.send_json(jsonable_encoder(message))
            except Exception:
                failed_connections.append(connection)
                logger.warning("WebSocket broadcast failed; pruning connection", exc_info=True)

        for connection in failed_connections:
            self.disconnect(connection)

manager = ConnectionManager()


def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _next_ws_sequence(app: FastAPI) -> int:
    current = int(getattr(app.state, "ws_sequence", 0)) + 1
    app.state.ws_sequence = current
    return current


def _build_ws_event_payload(app: FastAPI, event_type: str, data: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "version": "1",
        "type": event_type,
        "timestamp": _utcnow_iso(),
        "event_id": str(uuid.uuid4()),
        "sequence": _next_ws_sequence(app),
        "data": data or {},
    }


def _runtime_status_payload(app: FastAPI) -> dict[str, Any]:
    orchestrator = getattr(app.state, "orchestrator", None)
    arena_worker = getattr(app.state, "arena_worker", None)
    twitch_listener = getattr(app.state, "twitch_listener", None)
    director = getattr(app.state, "demo_director", None)

    mode = "director" if getattr(director, "is_running", False) else "autonomous"
    return {
        "phase": "runtime_snapshot",
        "timestamp": _utcnow_iso(),
        "mode": mode,
        "orchestrator_running": bool(getattr(orchestrator, "is_running", False)),
        "arena_worker_running": bool(getattr(arena_worker, "is_running", False)),
        "twitch_listener_running": bool(getattr(twitch_listener, "is_running", False)),
        "director": director.status_snapshot() if director else None,
        "websocket": {
            "active_connections": len(manager.active_connections),
            "next_sequence": int(getattr(app.state, "ws_sequence", 0)) + 1,
        },
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application."""
    logger.info("Lifespan startup begin")

    orchestrator = None
    arena_worker: AutonomousArenaWorker | None = None
    twitch_listener: TwitchListener | None = None
    demo_director: DemoDirector | None = None
    subscribed_ws_forwarder = False
    settings = get_settings()

    app.state.ws_sequence = 0
    app.state.orchestrator = None
    app.state.arena_worker = None
    app.state.twitch_listener = None
    app.state.demo_director = None

    async def stop_component(name: str, stop_callable):
        try:
            await stop_callable()
        except Exception:
            logger.exception("Failed to stop component: %s", name)

    # Pass EventBus messages to WebSocket clients
    async def ws_forwarder(event_type: str, data: dict | None):
        payload_data = data or {}
        try:
            await manager.broadcast(_build_ws_event_payload(app, event_type, payload_data))
        except Exception:
            logger.exception("Failed forwarding event_bus message to websockets (event_type=%s)", event_type)

    try:
        logger.info("Startup step: create database tables")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Startup step: initialize orchestrator")
        await initialize_orchestrator()
        orchestrator = get_orchestrator()
        app.state.orchestrator = orchestrator
        demo_director = DemoDirector(orchestrator, scenario_dir=settings.demo_scenario_dir)
        app.state.demo_director = demo_director

        logger.info("Startup step: start event bus")
        await event_bus.start()

        event_bus.subscribe("*", ws_forwarder)
        subscribed_ws_forwarder = True

        logger.info("Startup step: start orchestrator")
        await orchestrator.start()

        logger.info("Startup step: start arena worker")
        arena_worker = AutonomousArenaWorker(orchestrator, interval_seconds=15)
        await arena_worker.start()
        app.state.arena_worker = arena_worker

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
        app.state.twitch_listener = twitch_listener

        if settings.demo_director_enabled and settings.demo_director_autostart_scenario:
            logger.info(
                "Startup step: autostart Director Mode scenario (%s)",
                settings.demo_director_autostart_scenario,
            )
            try:
                await demo_director.start_scenario(
                    settings.demo_director_autostart_scenario,
                    restart_if_running=True,
                )
            except Exception:
                logger.exception("Director Mode autostart failed")

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

        if demo_director is not None:
            await stop_component("demo_director", demo_director.stop)

        if arena_worker is not None:
            await stop_component("arena_worker", arena_worker.stop)

        if orchestrator is not None:
            await stop_component("orchestrator", orchestrator.stop)

        await stop_component("event_bus", event_bus.stop)
        app.state.orchestrator = None
        app.state.arena_worker = None
        app.state.twitch_listener = None
        app.state.demo_director = None
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
app.include_router(demo_router, prefix="/api/demo", tags=["demo"])
app.include_router(state_router, prefix="/api/state", tags=["state"])


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


@app.get("/health/ready")
async def health_ready():
    """Readiness check with lightweight dependency status."""
    db_ready = False
    db_error: str | None = None
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ready = True
    except Exception as exc:
        db_error = str(exc)

    orchestrator = getattr(app.state, "orchestrator", None)
    director = getattr(app.state, "demo_director", None)
    arena_worker = getattr(app.state, "arena_worker", None)
    twitch_listener = getattr(app.state, "twitch_listener", None)

    components = {
        "db": {"ready": db_ready, "error": db_error},
        "orchestrator": {"ready": bool(getattr(orchestrator, "is_running", False))},
        "event_bus": {"ready": bool(getattr(event_bus, "is_started", False))},
        "arena_worker": {"ready": bool(getattr(arena_worker, "is_running", False))},
        "twitch_listener": {"ready": bool(getattr(twitch_listener, "is_running", False))},
        "demo_director": {"ready": director is not None, "running": bool(getattr(director, "is_running", False))},
    }
    overall = all(
        components[name]["ready"]
        for name in ("db", "orchestrator", "event_bus", "arena_worker", "twitch_listener")
    )
    return {
        "status": "ready" if overall else "degraded",
        "timestamp": _utcnow_iso(),
        "components": components,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        await websocket.send_json(_build_ws_event_payload(app, "system_status", _runtime_status_payload(app)))
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
