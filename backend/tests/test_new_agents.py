import pytest
import asyncio
from backend.ai_agents.agent import Agent, AgentRole, Message
from backend.ai_agents.orchestrator import SystemOrchestrator

@pytest.mark.asyncio
async def test_agent_initialization():
    agent = Agent(role=AgentRole.MODERATOR)
    assert agent.state.role == AgentRole.MODERATOR
    assert agent.state.is_active == True

@pytest.mark.asyncio
async def test_agent_processing():
    agent = Agent(role=AgentRole.DEBATER)
    msg = Message(sender_id="user", recipient_id=agent.state.agent_id, content="Hello")
    response = await agent.process_message(msg)
    assert response is not None
    assert response.sender_id == agent.state.agent_id
    # Since we used stub summarization, we check if content contains part of prompt or stub
    # For DEBATER, it uses "I argue that:"
    assert "I argue that:" in response.content

@pytest.mark.asyncio
async def test_orchestrator():
    orch = SystemOrchestrator()
    agent = Agent(role=AgentRole.ANALYST)
    orch.register_agent(agent)

    assert orch.get_agent(agent.state.agent_id) == agent

    msg = Message(sender_id="user", content="Broadcast", recipient_id=None) # Broadcast
    # We can't easily capture print output here without capsys, but we can ensure it runs without error
    await orch.broadcast_message(msg)

    # Clean up
    orch.remove_agent(agent.state.agent_id)
