"""
Agents API Router

API endpoints for AI agent management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..ai_agents.agent import Agent, AgentRole
from ..ai_agents.base_agent import AgentState
from ..ai_agents.orchestrator import SystemOrchestrator
from .dependencies import get_orchestrator

router = APIRouter()


class CreateAgentRequest(BaseModel):
    """Request to create an agent"""
    role: AgentRole
    name: str
    config: Optional[dict] = None


class AgentResponse(BaseModel):
    """Agent response model"""
    agent_id: str
    name: str
    role: str
    is_active: bool
    state: Dict[str, Any]


@router.get("/", response_model=List[AgentResponse])
async def list_agents(orchestrator: SystemOrchestrator = Depends(get_orchestrator)):
    """List all agents"""
    return [
        AgentResponse(
            agent_id=agent.state.agent_id,
            name=agent.name,
            role=agent.state.role,
            is_active=agent.state.is_active,
            state=agent.state.model_dump()
        )
        for agent in orchestrator.agents.values()
    ]


@router.post("/", response_model=AgentResponse)
async def create_agent(
    request: CreateAgentRequest,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """Create a new agent"""
    config = request.config or {}
    config["name"] = request.name

    agent = Agent(role=request.role, config=config)
    orchestrator.add_agent(agent)

    return AgentResponse(
        agent_id=agent.state.agent_id,
        name=agent.name,
        role=agent.state.role,
        is_active=agent.state.is_active,
        state=agent.state.model_dump()
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """Get agent by ID"""
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse(
        agent_id=agent.state.agent_id,
        name=agent.name,
        role=agent.state.role,
        is_active=agent.state.is_active,
        state=agent.state.model_dump()
    )


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """Delete an agent"""
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    orchestrator.remove_agent(agent_id)
    return {"status": "deleted", "agent_id": agent_id}


@router.post("/{agent_id}/activate")
async def activate_agent(
    agent_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """Activate an agent"""
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await agent.activate()
    return {"status": "activated", "agent_id": agent_id}


@router.post("/{agent_id}/deactivate")
async def deactivate_agent(
    agent_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """Deactivate an agent"""
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await agent.deactivate()
    return {"status": "deactivated", "agent_id": agent_id}
