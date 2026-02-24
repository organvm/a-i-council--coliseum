"""Contract tests for in-memory voting lifecycle."""

import pytest

from backend.ai_agents.orchestrator import SystemOrchestrator
from backend.voting.voting_engine import VoteType


@pytest.mark.asyncio
async def test_voting_session_create_vote_finalize_results():
    orchestrator = SystemOrchestrator()
    session = await orchestrator.create_voting_session(
        title="Adopt proposal",
        description="Vote now",
        vote_type=VoteType.MULTIPLE_CHOICE,
        options=["yes", "no"],
        duration_minutes=60,
    )

    vote = await orchestrator.cast_vote(
        session_id=session.session_id,
        user_id="user_1",
        choice="yes",
        tokens_staked=0.0,
    )
    assert vote.user_id == "user_1"

    with pytest.raises(ValueError, match="already voted"):
        await orchestrator.cast_vote(
            session_id=session.session_id,
            user_id="user_1",
            choice="yes",
            tokens_staked=0.0,
        )

    results = orchestrator.finalize_voting_session(session.session_id)
    assert "total_votes" in results

    stored_results = orchestrator.get_voting_results(session.session_id)
    assert stored_results is not None
    assert stored_results["total_votes"] == 1

    with pytest.raises(ValueError, match="not active"):
        await orchestrator.cast_vote(
            session_id=session.session_id,
            user_id="user_2",
            choice="yes",
            tokens_staked=0.0,
        )


@pytest.mark.asyncio
async def test_voting_rejects_invalid_choice_and_insufficient_stake():
    orchestrator = SystemOrchestrator()
    session = await orchestrator.create_voting_session(
        title="Pick one",
        description="choice test",
        vote_type=VoteType.MULTIPLE_CHOICE,
        options=["a", "b"],
        min_stake=10.0,
    )

    with pytest.raises(ValueError, match="Insufficient stake"):
        await orchestrator.cast_vote(
            session_id=session.session_id,
            user_id="user_3",
            choice="a",
            tokens_staked=0.0,
        )

    with pytest.raises(ValueError, match="Invalid vote choice"):
        await orchestrator.cast_vote(
            session_id=session.session_id,
            user_id="user_3",
            choice="c",
            tokens_staked=10.0,
        )

