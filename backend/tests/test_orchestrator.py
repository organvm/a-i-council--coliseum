"""Contract tests for SystemOrchestrator."""

import pytest
import asyncio

from backend.ai_agents.agent import Agent
from backend.ai_agents.base_agent import AgentRole
from backend.ai_agents.orchestrator import SystemOrchestrator


def test_add_get_list_remove_agent():
    orchestrator = SystemOrchestrator()
    agent = Agent(role=AgentRole.MODERATOR, config={"name": "ModBot"})

    agent_id = orchestrator.add_agent(agent)
    assert agent_id == agent.state.agent_id
    assert orchestrator.get_agent(agent_id) is agent
    assert any(a.state.agent_id == agent_id for a in orchestrator.list_agents())

    removed = orchestrator.remove_agent(agent_id)
    assert removed is True
    assert orchestrator.get_agent(agent_id) is None


@pytest.mark.asyncio
async def test_orchestrator_lifecycle_start_stop():
    orchestrator = SystemOrchestrator()

    assert orchestrator.is_running is False
    await orchestrator.start()
    assert orchestrator.is_running is True
    assert orchestrator.loop_task is not None
    assert orchestrator.communication_task is not None

    await asyncio.wait_for(orchestrator.stop(), timeout=2.0)
    assert orchestrator.is_running is False
    assert orchestrator.loop_task is None or orchestrator.loop_task.done()
    assert orchestrator.communication_task is None or orchestrator.communication_task.done()


@pytest.mark.asyncio
async def test_broadcast_event_reaches_agent_memory():
    print("test_broadcast: start")
    orchestrator = SystemOrchestrator()
    agent = Agent(role=AgentRole.DEBATER, config={"name": "Alice"})
    orchestrator.add_agent(agent)

    print("test_broadcast: orchestrator start")
    await orchestrator.start()
    print("test_broadcast: broadcasting event")
    await orchestrator.broadcast_event("New topic: AI Safety")
    print("test_broadcast: sleeping")
    await asyncio.sleep(0.1)
    
    print("test_broadcast: stopping orchestrator")
    await asyncio.wait_for(orchestrator.stop(), timeout=2.0)
    print("test_broadcast: orchestrator stopped")

    memories = agent.memory_manager.get_short_term(limit=10)
    print(f"test_broadcast: memories {memories}")
    assert any(
        m["content"]["content"] == "New topic: AI Safety"
        and m["content"]["sender_id"] == "SYSTEM"
        for m in memories
    )
    print("test_broadcast: end")
