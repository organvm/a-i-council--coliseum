
import pytest
from pydantic import ValidationError
from backend.api.blockchain import StakeRequest, TransferRequest
from backend.api.voting import CreateVotingSessionRequest, CastVoteRequest, VoteType

def test_blockchain_stake_validation():
    # Valid
    StakeRequest(amount=10, lock_period_days=5)

    # Invalid amount
    with pytest.raises(ValidationError):
        StakeRequest(amount=-10, lock_period_days=5)

    with pytest.raises(ValidationError):
        StakeRequest(amount=0, lock_period_days=5)

    # Invalid lock period
    with pytest.raises(ValidationError):
        StakeRequest(amount=10, lock_period_days=-1)

def test_blockchain_transfer_validation():
    # Valid
    TransferRequest(to_address="0x123", amount=50)

    # Invalid amount
    with pytest.raises(ValidationError):
        TransferRequest(to_address="0x123", amount=-50)

    with pytest.raises(ValidationError):
        TransferRequest(to_address="0x123", amount=0)

    # Invalid address
    with pytest.raises(ValidationError):
        TransferRequest(to_address="", amount=50)

    with pytest.raises(ValidationError):
        TransferRequest(to_address="   ", amount=50)

def test_voting_session_validation():
    # Valid
    CreateVotingSessionRequest(
        title="Valid",
        description="Desc",
        vote_type=VoteType.BINARY,
        options=["Yes", "No"],
        duration_minutes=60
    )

    # Invalid duration
    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Invalid",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=["Yes", "No"],
            duration_minutes=0
        )

    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Invalid",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=["Yes", "No"],
            duration_minutes=-10
        )

    # Invalid options (too few)
    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Invalid",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=["Yes"],
            duration_minutes=60
        )

    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Invalid",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=[],
            duration_minutes=60
        )

    # Invalid options (too many)
    with pytest.raises(ValidationError):
        CreateVotingSessionRequest(
            title="Invalid",
            description="Desc",
            vote_type=VoteType.BINARY,
            options=["Opt" + str(i) for i in range(21)],
            duration_minutes=60
        )

def test_cast_vote_validation():
    # Valid
    CastVoteRequest(choice="Yes", tokens_staked=0)
    CastVoteRequest(choice="Yes", tokens_staked=10)

    # Invalid stake
    with pytest.raises(ValidationError):
        CastVoteRequest(choice="Yes", tokens_staked=-1)
