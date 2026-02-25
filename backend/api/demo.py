"""
Demo API Router.

Controls local Director Mode scenarios used for deterministic demo capture.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..ai_agents.orchestrator import SystemOrchestrator
from ..settings import get_settings
from .dependencies import get_orchestrator

router = APIRouter()


class StartScenarioRequest(BaseModel):
    restart_if_running: bool = True
    speed_multiplier: float = Field(default=1.0, gt=0.0, le=10.0)


def _get_director_from_request(request: Request) -> Any:
    director = getattr(request.app.state, "demo_director", None)
    if director is None:
        raise HTTPException(status_code=503, detail="Demo director is not initialized")
    return director


@router.get("/scenarios")
async def list_scenarios(request: Request):
    director = _get_director_from_request(request)
    settings = get_settings()
    return {
        "director_enabled": settings.demo_director_enabled,
        "autostart_scenario": settings.demo_director_autostart_scenario,
        "scenarios": director.list_scenarios(),
        "status": director.status_snapshot(),
    }


@router.get("/status")
async def demo_status(request: Request):
    director = _get_director_from_request(request)
    return director.status_snapshot()


@router.post("/scenarios/{scenario_name}/start")
async def start_scenario(
    scenario_name: str,
    payload: StartScenarioRequest,
    request: Request,
    _orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    director = _get_director_from_request(request)
    try:
        status = await director.start_scenario(
            scenario_name,
            restart_if_running=payload.restart_if_running,
            speed_multiplier=payload.speed_multiplier,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"message": "Director Mode scenario started", "director": status}


@router.post("/reset")
async def reset_demo_runtime(
    request: Request,
    _orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    settings = get_settings()
    if not settings.is_development or not settings.demo_local_reset_enabled:
        raise HTTPException(status_code=403, detail="Demo reset is only enabled in local development")

    director = _get_director_from_request(request)
    status = await director.reset_runtime()
    return {"message": "Runtime demo state reset", "director": status}
