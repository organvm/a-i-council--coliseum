"""Alembic smoke test for schema upgrades on SQLite."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa


def _create_legacy_voting_tables(db_path: Path) -> None:
    engine = sa.create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE voting_sessions (
              id VARCHAR(36) PRIMARY KEY,
              title VARCHAR(255) NOT NULL,
              description TEXT NOT NULL,
              vote_type VARCHAR(50) NOT NULL,
              options JSON NOT NULL,
              status VARCHAR(20) NOT NULL,
              starts_at DATETIME NOT NULL,
              ends_at DATETIME,
              min_stake FLOAT DEFAULT 0.0,
              reward_pool FLOAT DEFAULT 0.0,
              results JSON
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE votes (
              id VARCHAR(36) PRIMARY KEY,
              session_id VARCHAR(36) NOT NULL,
              user_id INTEGER NOT NULL,
              choice JSON NOT NULL,
              weight FLOAT DEFAULT 1.0,
              tokens_staked FLOAT DEFAULT 0.0,
              timestamp DATETIME NOT NULL
            )
            """
        )


def test_alembic_upgrade_head_adds_voting_indexes_and_constraints(tmp_path, monkeypatch):
    pytest.importorskip("alembic")
    from alembic import command
    from alembic.config import Config

    db_path = tmp_path / "alembic-smoke.db"
    _create_legacy_voting_tables(db_path)

    async_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", async_url)

    cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(cfg, "head")

    engine = sa.create_engine(f"sqlite:///{db_path}")
    inspector = sa.inspect(engine)

    voting_session_indexes = {idx["name"] for idx in inspector.get_indexes("voting_sessions")}
    assert "ix_voting_sessions_status_starts_at" in voting_session_indexes

    vote_indexes = inspector.get_indexes("votes")
    vote_index_names = {idx["name"] for idx in vote_indexes}
    assert "ix_votes_session_timestamp" in vote_index_names

    unique_constraints = inspector.get_unique_constraints("votes")
    unique_names = {c.get("name") for c in unique_constraints}
    unique_vote_pair_index = any(
        idx.get("unique") and idx.get("column_names") == ["session_id", "user_id"]
        for idx in vote_indexes
    )
    assert "uq_votes_session_user" in unique_names or unique_vote_pair_index

    with engine.connect() as conn:
        revision = conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one()
    assert revision == "20260225_0001"
