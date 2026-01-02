"""
Tests for System Orchestrator
"""

import pytest
import asyncio
from backend.ai_agents.orchestrator import SystemOrchestrator
from backend.ai_agents.agent import Agent, AgentRole

@pytest.fixture
def orchestrator():
    return SystemOrchestrator()

@pytest.mark.asyncio
async def test_orchestrator_add_remove_agent(orchestrator):
    agent = Agent(role=AgentRole.MODERATOR, config={"name": "ModBot"})

    orchestrator.add_agent(agent)
    assert agent.state.agent_id in orchestrator.agents
    assert agent.state.agent_id in orchestrator.communication_protocol.agents

    orchestrator.remove_agent(agent.state.agent_id)
    assert agent.state.agent_id not in orchestrator.agents
    assert agent.state.agent_id not in orchestrator.communication_protocol.agents

@pytest.mark.asyncio
async def test_orchestrator_lifecycle(orchestrator):
    assert not orchestrator.is_running

    await orchestrator.start()
    assert orchestrator.is_running
    assert orchestrator.loop_task is not None
    assert not orchestrator.loop_task.done()

    await orchestrator.stop()
    assert not orchestrator.is_running
    assert orchestrator.loop_task.cancelled() or orchestrator.loop_task.done()

@pytest.mark.asyncio
async def test_orchestrator_broadcast(orchestrator):
    await orchestrator.start()

    # Create two agents
    agent1 = Agent(role=AgentRole.DEBATER, config={"name": "Alice"})
    agent2 = Agent(role=AgentRole.DEBATER, config={"name": "Bob"})

    orchestrator.add_agent(agent1)
    orchestrator.add_agent(agent2)

    # Broadcast message
    await orchestrator.broadcast_event("New topic: AI Safety")

    # Give some time for message processing
    await asyncio.sleep(0.1)

    # Agents should have received the message (stored in short term memory)
    # We check agent1's history or memory
    # Note: process_message adds to memory_manager

    memories1 = agent1.memory_manager.get_short_term(limit=5)
    found = False
    for m in memories1:
        if m["content"]["content"] == "New topic: AI Safety" and m["content"]["sender_id"] == "SYSTEM":
            found = True
            break
    assert found

    await orchestrator.stop()
