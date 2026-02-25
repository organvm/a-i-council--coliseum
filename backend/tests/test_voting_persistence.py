"""Restart-consistency tests for persisted voting state."""

import pytest

from backend.database import AsyncSessionLocal, Base, engine
from backend.models import User
from backend.voting.voting_engine import VoteStatus, VoteType, VotingEngine


@pytest.mark.asyncio
async def test_voting_engine_reload_restores_votes_and_final_results():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        db.add(
            User(
                id=1,
                username="persist_user",
                email="persist_user@example.test",
                hashed_password="not-used",
            )
        )
        await db.commit()

    engine_one = VotingEngine()
    session = await engine_one.create_session(
        title="Restart safety poll",
        description="Verify voting state reloads after process restart",
        vote_type=VoteType.MULTIPLE_CHOICE,
        options=["alpha", "beta"],
        duration_minutes=15,
    )
    await engine_one.start_session(session.session_id)

    vote = engine_one.cast_vote(
        session_id=session.session_id,
        user_id="1",
        choice="alpha",
        weight=1.0,
        tokens_staked=0.0,
    )
    assert vote is not None
    await engine_one.persist_vote(vote)
    await engine_one.finalize_session_and_persist(session.session_id)

    engine_two = VotingEngine()
    await engine_two.load_active_sessions()

    restored = engine_two.sessions.get(session.session_id)
    assert restored is not None
    assert restored.status == VoteStatus.FINALIZED
    assert restored.results is not None
    assert restored.results["total_votes"] == 1
    assert len(restored.votes) == 1
    assert restored.votes[0].vote_id == vote.vote_id
    assert restored.votes[0].user_id == "1"
    assert engine_two.get_user_votes("1")[0].vote_id == vote.vote_id
