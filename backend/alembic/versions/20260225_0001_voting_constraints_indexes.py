"""Add voting constraints and indexes for durable persistence.

Revision ID: 20260225_0001
Revises: None
Create Date: 2026-02-25 09:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260225_0001"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "voting_sessions"):
        voting_session_indexes = {idx["name"] for idx in inspector.get_indexes("voting_sessions")}
        if "ix_voting_sessions_status_starts_at" not in voting_session_indexes:
            op.create_index(
                "ix_voting_sessions_status_starts_at",
                "voting_sessions",
                ["status", "starts_at"],
                unique=False,
            )

    if _has_table(inspector, "votes"):
        vote_indexes = {idx["name"] for idx in inspector.get_indexes("votes")}
        vote_uniques = {c.get("name") for c in inspector.get_unique_constraints("votes")}

        need_vote_index = "ix_votes_session_timestamp" not in vote_indexes
        need_vote_unique = "uq_votes_session_user" not in vote_uniques

        if bind.dialect.name == "sqlite":
            if need_vote_index or need_vote_unique:
                with op.batch_alter_table("votes") as batch_op:
                    if need_vote_unique:
                        batch_op.create_unique_constraint(
                            "uq_votes_session_user",
                            ["session_id", "user_id"],
                        )
                    if need_vote_index:
                        batch_op.create_index(
                            "ix_votes_session_timestamp",
                            ["session_id", "timestamp"],
                            unique=False,
                        )
        else:
            if need_vote_unique:
                op.create_unique_constraint(
                    "uq_votes_session_user",
                    "votes",
                    ["session_id", "user_id"],
                )
            if need_vote_index:
                op.create_index(
                    "ix_votes_session_timestamp",
                    "votes",
                    ["session_id", "timestamp"],
                    unique=False,
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "votes"):
        vote_indexes = {idx["name"] for idx in inspector.get_indexes("votes")}
        vote_uniques = {c.get("name") for c in inspector.get_unique_constraints("votes")}
        has_vote_index = "ix_votes_session_timestamp" in vote_indexes
        has_vote_unique = "uq_votes_session_user" in vote_uniques

        if bind.dialect.name == "sqlite":
            if has_vote_index or has_vote_unique:
                with op.batch_alter_table("votes") as batch_op:
                    if has_vote_index:
                        batch_op.drop_index("ix_votes_session_timestamp")
                    if has_vote_unique:
                        batch_op.drop_constraint("uq_votes_session_user", type_="unique")
        else:
            if has_vote_index:
                op.drop_index("ix_votes_session_timestamp", table_name="votes")
            if has_vote_unique:
                op.drop_constraint("uq_votes_session_user", "votes", type_="unique")

    if _has_table(inspector, "voting_sessions"):
        voting_session_indexes = {idx["name"] for idx in inspector.get_indexes("voting_sessions")}
        if "ix_voting_sessions_status_starts_at" in voting_session_indexes:
            op.drop_index("ix_voting_sessions_status_starts_at", table_name="voting_sessions")
