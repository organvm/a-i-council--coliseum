"""
Security Validation Tests.

Ensures API models correctly reject invalid or malicious inputs.
"""

import pytest
from pydantic import ValidationError
from backend.api.blockchain import StakeRequest
from backend.api.voting import CreateVotingSessionRequest, CastVoteRequest, VoteType
from backend.api.agents import CreateAgentRequest, AgentRole

def test_stake_request_validation():
    """Assert StakeRequest rejects negative or zero amounts."""
    with pytest.raises(ValidationError):
        StakeRequest(amount=-10.5)
    with pytest.raises(ValidationError):
        StakeRequest(amount=0)
    
    # Valid
    req = StakeRequest(amount=10.5, lock_period_days=7)
    assert req.amount == 10.5
    assert req.lock_period_days == 7

def test_voting_session_validation():
    """Assert CreateVotingSessionRequest enforces constraints."""
    # Title too short
    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="abc",
            description="Valid description length here",
            vote_type=VoteType.MULTIPLE_CHOICE,
            options=["A", "B"]
        )
    
    # Too few options
    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Valid Title",
            description="Valid description length here",
            vote_type=VoteType.MULTIPLE_CHOICE,
            options=["Only One"]
        )
    
    # Negative duration
    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Valid Title",
            description="Valid description length here",
            vote_type=VoteType.MULTIPLE_CHOICE,
            options=["A", "B"],
            duration_minutes=-10
        )

def test_cast_vote_validation():
    """Assert CastVoteRequest rejects negative stakes."""
    with pytest.raises(ValidationError):
        CastVoteRequest(choice="A", tokens_staked=-1.0)
    
    # Valid zero stake
    req = CastVoteRequest(choice="A", tokens_staked=0.0)
    assert req.tokens_staked == 0.0

def test_create_agent_validation():
    """Assert CreateAgentRequest enforces name length."""
    # Empty name
    with pytest.raises(ValidationError):
        CreateAgentRequest(role=AgentRole.DEBATER, name="")
    
    # Name too long
    with pytest.raises(ValidationError):
        CreateAgentRequest(role=AgentRole.DEBATER, name="A" * 51)
    
    # Valid
    req = CreateAgentRequest(role=AgentRole.DEBATER, name="Socrates")
    assert req.name == "Socrates"
