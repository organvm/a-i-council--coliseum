"""Contract tests for concrete Agent behavior."""

import pytest

from backend.ai_agents.agent import Agent
from backend.ai_agents.base_agent import AgentRole, Message


@pytest.mark.asyncio
async def test_direct_message_generates_direct_response():
    agent = Agent(role=AgentRole.DEBATER, config={"name": "TestDebater"})
    message = Message(
        sender_id="user_1",
        recipient_id=agent.state.agent_id,
        content="Hello there",
    )

    response = await agent.process_message(message)

    assert response is not None
    assert response.sender_id == agent.state.agent_id
    assert response.recipient_id == "user_1"


@pytest.mark.asyncio
async def test_broadcast_message_with_name_mention_gets_response():
    agent = Agent(role=AgentRole.MODERATOR, config={"name": "Atlas"})
    message = Message(
        sender_id="user_1",
        recipient_id=None,
        content="Atlas, can you moderate this?",
    )

    response = await agent.process_message(message)

    assert response is not None
    assert response.sender_id == agent.state.agent_id
    assert response.recipient_id is None


@pytest.mark.asyncio
async def test_unmentioned_non_debater_broadcast_is_ignored():
    agent = Agent(role=AgentRole.ANALYST, config={"name": "Athena"})
    message = Message(
        sender_id="user_2",
        recipient_id=None,
        content="General channel update",
    )

    response = await agent.process_message(message)

    assert response is None

