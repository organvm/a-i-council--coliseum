"""
Agents API Router.

API endpoints for AI agent management.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..ai_agents.agent import Agent, AgentRole
from ..ai_agents.orchestrator import SystemOrchestrator
from ..models import User
from .dependencies import get_orchestrator
from .mutation_controls import guard_agent_mutation

router = APIRouter()
AGENT_NOT_FOUND_RESPONSE = {404: {"description": "Agent not found"}}
AGENT_MUTATION_RESPONSES = {
    **AGENT_NOT_FOUND_RESPONSE,
    401: {"description": "Authentication required"},
    403: {"description": "Forbidden (inactive user or policy denial)"},
    429: {"description": "Rate limit exceeded"},
}


class CreateAgentRequest(BaseModel):
    """Request to create an agent."""

    role: AgentRole
    name: str = Field(min_length=1, max_length=50)
    config: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Agent response model."""

    agent_id: str
    name: str
    role: str
    is_active: bool
    state: Dict[str, Any]


@router.get("/", response_model=List[AgentResponse])
async def list_agents(orchestrator: SystemOrchestrator = Depends(get_orchestrator)):
    """List all agents."""
    return [
        AgentResponse(
            agent_id=agent.state.agent_id,
            name=agent.name,
            role=agent.state.role.value,
            is_active=agent.state.is_active,
            state=agent.state.model_dump(),
        )
        for agent in orchestrator.list_agents()
    ]


@router.post("/", response_model=AgentResponse, responses=AGENT_MUTATION_RESPONSES)
async def create_agent(
    request: CreateAgentRequest,
    _current_user: User = Depends(guard_agent_mutation),
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Create a new agent."""
    config = request.config or {}
    config["name"] = request.name

    agent = Agent(role=request.role, config=config)
    orchestrator.add_agent(agent)

    return AgentResponse(
        agent_id=agent.state.agent_id,
        name=agent.name,
        role=agent.state.role.value,
        is_active=agent.state.is_active,
        state=agent.state.model_dump(),
    )


@router.get("/{agent_id}", response_model=AgentResponse, responses=AGENT_NOT_FOUND_RESPONSE)
async def get_agent(
    agent_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Get agent by ID."""
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse(
        agent_id=agent.state.agent_id,
        name=agent.name,
        role=agent.state.role.value,
        is_active=agent.state.is_active,
        state=agent.state.model_dump(),
    )


@router.get("/{agent_id}/memory", responses=AGENT_NOT_FOUND_RESPONSE)
async def get_agent_memory(
    agent_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Get memory snapshots for a specific agent."""
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "agent_id": agent_id,
        "short_term": agent.memory_manager.get_short_term(limit=25),
        "long_term_stats": agent.memory_manager.get_stats(),
        "state_memory": agent.state.memory,
    }


@router.delete("/{agent_id}", responses=AGENT_MUTATION_RESPONSES)
async def delete_agent(
    agent_id: str,
    _current_user: User = Depends(guard_agent_mutation),
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Delete an agent."""
    if not orchestrator.remove_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "deleted", "agent_id": agent_id}


@router.post("/{agent_id}/activate", responses=AGENT_MUTATION_RESPONSES)
async def activate_agent(
    agent_id: str,
    _current_user: User = Depends(guard_agent_mutation),
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Activate an agent."""
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await agent.activate()
    return {"status": "activated", "agent_id": agent_id}


@router.post("/{agent_id}/deactivate", responses=AGENT_MUTATION_RESPONSES)
async def deactivate_agent(
    agent_id: str,
    _current_user: User = Depends(guard_agent_mutation),
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
):
    """Deactivate an agent."""
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await agent.deactivate()
    return {"status": "deactivated", "agent_id": agent_id}
