import pytest
from pydantic import ValidationError
from backend.api.blockchain import StakeRequest, TransferRequest
from backend.api.voting import CreateVotingSessionRequest, CastVoteRequest
from backend.voting.voting_engine import VoteType
from backend.api.agents import CreateAgentRequest
from backend.ai_agents.base_agent import AgentRole

def test_stake_request_validation():
    """Verify validation for StakeRequest"""
    # Should fail with negative amount
    with pytest.raises(ValidationError):
        StakeRequest(amount=-100, lock_period_days=0)

    # Should fail with zero amount (stake must be positive)
    with pytest.raises(ValidationError):
        StakeRequest(amount=0, lock_period_days=0)

    # Should fail with negative lock period
    with pytest.raises(ValidationError):
        StakeRequest(amount=100, lock_period_days=-1)

def test_transfer_request_validation():
    """Verify validation for TransferRequest"""
    # Should fail with negative amount
    with pytest.raises(ValidationError):
        TransferRequest(to_address="addr", amount=-50)

    # Should fail with zero amount
    with pytest.raises(ValidationError):
        TransferRequest(to_address="addr", amount=0)

    # Should fail with empty address
    with pytest.raises(ValidationError):
        TransferRequest(to_address="", amount=50)

def test_create_voting_session_validation():
    """Verify validation for CreateVotingSessionRequest"""
    # Should fail with empty options
    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Test",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=[],
            duration_minutes=60
        )

    # Should fail with too few options
    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Test",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=["One"],
            duration_minutes=60
        )

    # Should fail with too many options (DoS protection)
    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Test",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=["Opt"] * 21,
            duration_minutes=60
        )

    # Should fail with non-positive duration
    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Test",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=["Yes", "No"],
            duration_minutes=0
        )

def test_cast_vote_request_validation():
    """Verify validation for CastVoteRequest"""
    # Should fail with negative stake
    with pytest.raises(ValidationError):
        CastVoteRequest(choice="Yes", tokens_staked=-1.0)

def test_create_agent_validation():
    """Verify validation for CreateAgentRequest"""
    # Should fail with empty name
    with pytest.raises(ValidationError):
        CreateAgentRequest(role=AgentRole.DEBATER, name="")

    # Should fail with whitespace name
    with pytest.raises(ValidationError):
        CreateAgentRequest(role=AgentRole.DEBATER, name="   ")

    # Should fail with name too long
    with pytest.raises(ValidationError):
        CreateAgentRequest(role=AgentRole.DEBATER, name="a" * 51)
