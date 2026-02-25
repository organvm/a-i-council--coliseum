"""Authz + rate-limit dependencies for mutating endpoints."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request

from ..infrastructure.rate_limiter import mutation_rate_limiter
from ..models import User
from ..settings import get_settings
from .auth import get_current_user, get_optional_current_user

logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = 10.0
VOTE_CAST_LIMIT = 60
VOTING_SESSION_CREATE_LIMIT = 15
EVENT_INGEST_LIMIT = 30
AGENT_MUTATION_LIMIT = 20
DEMO_SCENARIO_START_LIMIT = 8
DEMO_RESET_LIMIT = 5


@dataclass(frozen=True)
class MutationActor:
    """Request actor used for authz/rate-limit key generation."""

    user: User | None
    identifier: str
    source: str  # "user" or "client"
    demo_bypass: bool = False


def _client_host(request: Request) -> str:
    client = getattr(request, "client", None)
    host = getattr(client, "host", None)
    return host or "unknown"


def _actor_for_request(request: Request, user: User | None, *, demo_bypass: bool) -> MutationActor:
    if user is not None:
        return MutationActor(user=user, identifier=f"user:{user.id}", source="user", demo_bypass=demo_bypass)
    return MutationActor(user=None, identifier=f"client:{_client_host(request)}", source="client", demo_bypass=demo_bypass)


def _require_active_user(user: User) -> User:
    if getattr(user, "is_active", True) is False:
        raise HTTPException(status_code=403, detail="User account is inactive")
    return user


async def require_mutation_actor(
    request: Request,
    user: User | None = Depends(get_optional_current_user),
) -> MutationActor:
    """Require an active user unless local demo bypass is enabled."""
    settings = get_settings()
    if user is not None:
        _require_active_user(user)
        return _actor_for_request(request, user, demo_bypass=False)

    if settings.allow_local_unauthenticated_mutations:
        actor = _actor_for_request(request, None, demo_bypass=True)
        logger.info(
            "Allowing unauthenticated local mutation (path=%s actor=%s)",
            request.url.path,
            actor.identifier,
        )
        return actor

    raise HTTPException(status_code=401, detail="Authentication required for mutating endpoints")


async def require_rate_limited_vote_user(
    request: Request,
    user: User = Depends(get_current_user),
) -> User:
    """Require authenticated vote user and apply per-user/IP rate limit."""
    _require_active_user(user)
    actor = _actor_for_request(request, user, demo_bypass=False)
    await _enforce_rate_limit(request, "vote_cast", actor, limit=VOTE_CAST_LIMIT)
    return user


async def guard_voting_session_create(
    request: Request,
    actor: MutationActor = Depends(require_mutation_actor),
) -> MutationActor:
    """Authz + rate-limit guard for session creation."""
    await _enforce_rate_limit(
        request,
        "voting_session_create",
        actor,
        limit=VOTING_SESSION_CREATE_LIMIT,
    )
    return actor


async def guard_event_ingest(
    request: Request,
    actor: MutationActor = Depends(require_mutation_actor),
) -> MutationActor:
    """Authz + rate-limit guard for event ingestion."""
    await _enforce_rate_limit(request, "event_ingest", actor, limit=EVENT_INGEST_LIMIT)
    return actor


async def guard_agent_mutation(
    request: Request,
    user: User = Depends(get_current_user),
) -> User:
    """Require authenticated user for agent mutations and apply rate limit."""
    _require_active_user(user)
    actor = _actor_for_request(request, user, demo_bypass=False)
    await _enforce_rate_limit(
        request,
        "agent_mutation",
        actor,
        limit=AGENT_MUTATION_LIMIT,
    )
    return user


async def guard_demo_scenario_start(
    request: Request,
    actor: MutationActor = Depends(require_mutation_actor),
) -> MutationActor:
    """Guard for Director Mode scenario start."""
    await _enforce_rate_limit(
        request,
        "demo_scenario_start",
        actor,
        limit=DEMO_SCENARIO_START_LIMIT,
    )
    return actor


async def guard_demo_reset(
    request: Request,
    actor: MutationActor = Depends(require_mutation_actor),
) -> MutationActor:
    """Guard for local demo reset."""
    await _enforce_rate_limit(
        request,
        "demo_reset",
        actor,
        limit=DEMO_RESET_LIMIT,
    )
    return actor


async def _enforce_rate_limit(
    request: Request,
    action: str,
    actor: MutationActor,
    *,
    limit: int,
) -> None:
    key = f"{action}:{actor.identifier}"
    allowed = await mutation_rate_limiter.allow(
        key,
        limit=limit,
        window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    )
    if allowed:
        return

    logger.warning(
        "Rate limit exceeded (action=%s actor=%s path=%s source=%s demo_bypass=%s)",
        action,
        actor.identifier,
        request.url.path,
        actor.source,
        actor.demo_bypass,
    )
    raise HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded for {action}; retry later",
    )
