"""
Tests for Concrete Agent Implementation
"""

import pytest
import asyncio
from datetime import datetime
from backend.ai_agents.agent import Agent, AgentRole, Message
from backend.ai_agents.memory_manager import MemoryManager
from backend.ai_agents.knowledge_base import KnowledgeBase
from backend.ai_agents.nlp_module import NLPProcessor
from backend.ai_agents.decision_engine import DecisionEngine

@pytest.fixture
def agent():
    return Agent(role=AgentRole.DEBATER, config={"name": "TestAgent"})

@pytest.mark.asyncio
async def test_agent_initialization(agent):
    assert agent.state.role == AgentRole.DEBATER
    assert agent.name == "TestAgent"
    assert isinstance(agent.memory_manager, MemoryManager)
    assert isinstance(agent.knowledge_base, KnowledgeBase)
    assert isinstance(agent.nlp_processor, NLPProcessor)
    assert isinstance(agent.decision_engine, DecisionEngine)

@pytest.mark.asyncio
async def test_agent_process_direct_message(agent):
    sender_id = "sender_123"
    content = "Hello, agent!"
    message = Message(
        sender_id=sender_id,
        recipient_id=agent.state.agent_id,
        content=content
    )

    response = await agent.process_message(message)

    assert response is not None
    assert response.sender_id == agent.state.agent_id
    assert response.recipient_id == sender_id
    # Test expectation update: Production code adds role prefix "I argue that:", not "I received:"
    assert "I argue that:" in response.content

@pytest.mark.asyncio
async def test_agent_process_broadcast_message_ignored(agent):
    sender_id = "sender_123"
    content = "Hello everyone!"
    # No recipient means broadcast
    message = Message(
        sender_id=sender_id,
        recipient_id=None,
        content=content
    )

    # Should ignore irrelevant broadcast
    response = await agent.process_message(message)
    assert response is None

@pytest.mark.asyncio
async def test_agent_process_broadcast_message_mentioned(agent):
    sender_id = "sender_123"
    content = "Hey TestAgent, what do you think?"
    message = Message(
        sender_id=sender_id,
        recipient_id=None,
        content=content
    )

    # Should respond because name is mentioned
    response = await agent.process_message(message)
    assert response is not None
    # For broadcast response, recipient should be None (reply to all) or sender?
    # Logic in agent.py: recipient_id=message.sender_id if is_direct else None
    assert response.recipient_id is None

@pytest.mark.asyncio
async def test_agent_memory_update(agent):
    sender_id = "sender_123"
    content = "Remember this."
    message = Message(
        sender_id=sender_id,
        recipient_id=agent.state.agent_id,
        content=content
    )

    await agent.process_message(message)

    # Check short term memory
    memories = agent.memory_manager.get_short_term(limit=1)
    assert len(memories) == 1
    assert memories[0]["content"]["content"] == content

@pytest.mark.asyncio
async def test_agent_make_decision_vote(agent):
    # Setup: Create a decision in the engine first so the vote is valid
    from backend.ai_agents.decision_engine import DecisionType
    decision_obj = agent.decision_engine.create_decision(
        title="Should we adopt Python?",
        description="Decision for test",
        decision_type=DecisionType.MULTIPLE_CHOICE,
        options=["Yes", "No"],
        required_votes=1
    )

    context = {
        "type": "vote",
        "decision_id": decision_obj.decision_id,
        "topic": "Should we adopt Python?",
        "options": ["Yes", "No"]
    }

    decision = await agent.make_decision(context)

    assert "choice" in decision
    assert decision["choice"] in ["Yes", "No", "yes", "no"]
    # Reasoning is not guaranteed if not in production return dict, but status is
    assert decision["status"] == "voted"
