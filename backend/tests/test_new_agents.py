"""Backward-compatibility tests for orchestrator public aliases."""

import asyncio

import pytest

from backend.ai_agents.agent import Agent
from backend.ai_agents.base_agent import AgentRole, Message
from backend.ai_agents.orchestrator import SystemOrchestrator


def test_register_agent_alias_points_to_add_agent():
    orchestrator = SystemOrchestrator()
    agent = Agent(role=AgentRole.ANALYST)
    agent_id = orchestrator.register_agent(agent)

    assert agent_id == agent.state.agent_id
    assert orchestrator.get_agent(agent_id) is agent


@pytest.mark.asyncio
async def test_broadcast_message_accepts_message_object():
    orchestrator = SystemOrchestrator()
    agent = Agent(role=AgentRole.DEBATER, config={"name": "Echo"})
    orchestrator.add_agent(agent)

    await orchestrator.start()
    await orchestrator.broadcast_message(Message(sender_id="SYSTEM", content="Broadcast"))
    await asyncio.sleep(0.05)
    await asyncio.wait_for(orchestrator.stop(), timeout=2.0)

    memories = agent.memory_manager.get_short_term(limit=10)
    assert any(m["content"]["content"] == "Broadcast" for m in memories)
