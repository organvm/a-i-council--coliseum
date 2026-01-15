
import pytest
from pydantic import ValidationError
from backend.api.blockchain import StakeRequest, TransferRequest
from backend.api.voting import CreateVotingSessionRequest, CastVoteRequest, VoteType

def test_stake_request_validation():
    # Negative amount should fail
    with pytest.raises(ValidationError) as excinfo:
        StakeRequest(amount=-100, lock_period_days=0)
    assert "greater than 0" in str(excinfo.value)

    # Negative lock period should fail
    with pytest.raises(ValidationError) as excinfo:
        StakeRequest(amount=100, lock_period_days=-5)
    assert "greater than or equal to 0" in str(excinfo.value)

def test_voting_request_validation():
    # Empty options should fail
    with pytest.raises(ValidationError) as excinfo:
        CreateVotingSessionRequest(
            title="Test",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=[],
            duration_minutes=60
        )
    assert "at least 2 items" in str(excinfo.value)

    # Negative duration should fail
    with pytest.raises(ValidationError) as excinfo:
        CreateVotingSessionRequest(
            title="Test",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=["A", "B"],
            duration_minutes=-60
        )
    assert "greater than 0" in str(excinfo.value)

def test_cast_vote_validation():
    # Negative tokens should fail
    with pytest.raises(ValidationError) as excinfo:
        CastVoteRequest(choice="Yes", tokens_staked=-50)
    assert "greater than or equal to 0" in str(excinfo.value)
