"""Endpoint-level authz and rate-limit tests for mutation guards."""

from __future__ import annotations

from unittest.mock import patch
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.api import dependencies
from backend.api.auth import get_current_user, get_optional_current_user
from backend.infrastructure.rate_limiter import mutation_rate_limiter
from backend.main import app
from backend.models import User
from backend.settings import get_settings
from backend.voting.voting_engine import VoteStatus, VoteType, VotingSession


@pytest.fixture(autouse=True)
def clear_settings_and_limiter():
    get_settings.cache_clear()
    mutation_rate_limiter.clear_sync()
    yield
    get_settings.cache_clear()
    mutation_rate_limiter.clear_sync()
    app.dependency_overrides.clear()
    dependencies._orchestrator_instance = None


@pytest.fixture
def client_no_auth():
    class _StubOrchestrator:
        def __init__(self):
            self.agents = {}
            self.is_running = False

        async def start(self):
            return None

        async def stop(self):
            return None

        async def ingest_event(self, *args, **kwargs):
            return None

        async def create_voting_session(self, **kwargs):
            session = VotingSession(
                title=kwargs["title"],
                description=kwargs["description"],
                vote_type=kwargs["vote_type"],
                options=kwargs["options"],
                duration_minutes=kwargs.get("duration_minutes", 60),
                min_stake=kwargs.get("min_stake", 0.0),
            )
            session.status = VoteStatus.ACTIVE
            session.starts_at = datetime.utcnow()
            session.ends_at = session.starts_at + timedelta(minutes=session.duration_minutes)
            return session

        def get_voting_session(self, session_id: str):
            return None

        def add_agent(self, agent):
            self.agents[agent.state.agent_id] = agent
            return agent.state.agent_id

    async def _noop_initialize():
        return None

    stub = _StubOrchestrator()
    dependencies._orchestrator_instance = stub
    with patch("backend.main.initialize_orchestrator", side_effect=_noop_initialize), patch(
        "backend.main.get_orchestrator", side_effect=lambda: stub
    ), patch("backend.ai_agents.orchestrator.SystemOrchestrator.start"), patch(
        "backend.ai_agents.orchestrator.SystemOrchestrator.stop"
    ), TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_with_auth():
    class _StubOrchestrator:
        def __init__(self):
            self.agents = {}
            self.is_running = False

        async def start(self):
            return None

        async def stop(self):
            return None

        async def ingest_event(self, *args, **kwargs):
            return None

        async def create_voting_session(self, **kwargs):
            session = VotingSession(
                title=kwargs["title"],
                description=kwargs["description"],
                vote_type=kwargs["vote_type"],
                options=kwargs["options"],
                duration_minutes=kwargs.get("duration_minutes", 60),
                min_stake=kwargs.get("min_stake", 0.0),
            )
            session.status = VoteStatus.ACTIVE
            session.starts_at = datetime.utcnow()
            session.ends_at = session.starts_at + timedelta(minutes=session.duration_minutes)
            return session

        def get_voting_session(self, session_id: str):
            return None

        def add_agent(self, agent):
            self.agents[agent.state.agent_id] = agent
            return agent.state.agent_id

    async def _noop_initialize():
        return None

    stub = _StubOrchestrator()
    dependencies._orchestrator_instance = stub
    app.dependency_overrides[get_current_user] = lambda: User(
        id=1,
        username="test",
        email="test@test.com",
        is_active=True,
    )
    with patch("backend.main.initialize_orchestrator", side_effect=_noop_initialize), patch(
        "backend.main.get_orchestrator", side_effect=lambda: stub
    ), patch("backend.ai_agents.orchestrator.SystemOrchestrator.start"), patch(
        "backend.ai_agents.orchestrator.SystemOrchestrator.stop"
    ), TestClient(app) as test_client:
        yield test_client


def _session_payload(suffix: str = "") -> dict:
    return {
        "title": f"Choose direction{suffix}",
        "description": "direction vote payload",
        "vote_type": "multiple_choice",
        "options": ["alpha", "beta"],
        "duration_minutes": 60,
        "min_stake": 0.0,
    }


def test_create_session_requires_auth_when_demo_bypass_disabled(monkeypatch, client_no_auth: TestClient):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEMO_ALLOW_UNAUTHENTICATED_MUTATIONS", "false")
    get_settings.cache_clear()

    resp = client_no_auth.post("/api/voting/sessions", json=_session_payload())
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]


def test_event_ingest_requires_auth_when_demo_bypass_disabled(monkeypatch, client_no_auth: TestClient):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEMO_ALLOW_UNAUTHENTICATED_MUTATIONS", "false")
    get_settings.cache_clear()

    resp = client_no_auth.post(
        "/api/events/ingest",
        json={"source": "api", "data": {"title": "Policy Update", "description": "new policy"}},
    )
    assert resp.status_code == 401


def test_inactive_authenticated_user_forbidden_for_session_create(client_no_auth: TestClient):
    app.dependency_overrides[get_optional_current_user] = lambda: User(
        id=9,
        username="inactive",
        email="inactive@example.test",
        is_active=False,
    )

    resp = client_no_auth.post("/api/voting/sessions", json=_session_payload("-inactive"))
    assert resp.status_code == 403
    assert "inactive" in resp.json()["detail"].lower()


def test_session_create_rate_limited_with_local_demo_bypass(monkeypatch, client_no_auth: TestClient):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DEMO_ALLOW_UNAUTHENTICATED_MUTATIONS", "true")
    get_settings.cache_clear()

    import backend.api.mutation_controls as mutation_controls

    monkeypatch.setattr(mutation_controls, "VOTING_SESSION_CREATE_LIMIT", 1)
    monkeypatch.setattr(mutation_controls, "RATE_LIMIT_WINDOW_SECONDS", 60.0)

    first = client_no_auth.post("/api/voting/sessions", json=_session_payload("-rl1"))
    second = client_no_auth.post("/api/voting/sessions", json=_session_payload("-rl2"))

    assert first.status_code == 200
    assert second.status_code == 429
    assert "Rate limit exceeded" in second.json()["detail"]


def test_vote_cast_rate_limited_for_authenticated_user(monkeypatch, client_with_auth: TestClient):
    import backend.api.mutation_controls as mutation_controls

    monkeypatch.setattr(mutation_controls, "VOTE_CAST_LIMIT", 1)
    monkeypatch.setattr(mutation_controls, "RATE_LIMIT_WINDOW_SECONDS", 60.0)

    first = client_with_auth.post(
        "/api/voting/sessions/missing-session/vote",
        json={"choice": "alpha", "tokens_staked": 0.0},
    )
    second = client_with_auth.post(
        "/api/voting/sessions/missing-session/vote",
        json={"choice": "alpha", "tokens_staked": 0.0},
    )

    assert first.status_code == 404
    assert second.status_code == 429


def test_agent_create_requires_authentication(client_no_auth: TestClient):
    resp = client_no_auth.post(
        "/api/agents/",
        json={"role": "analyst", "name": "Unauthed Agent", "config": {}},
    )
    assert resp.status_code == 401


def test_agent_create_rate_limited_for_authenticated_user(monkeypatch, client_with_auth: TestClient):
    import backend.api.mutation_controls as mutation_controls

    monkeypatch.setattr(mutation_controls, "AGENT_MUTATION_LIMIT", 1)
    monkeypatch.setattr(mutation_controls, "RATE_LIMIT_WINDOW_SECONDS", 60.0)

    first = client_with_auth.post(
        "/api/agents/",
        json={"role": "analyst", "name": "Agent One", "config": {}},
    )
    second = client_with_auth.post(
        "/api/agents/",
        json={"role": "analyst", "name": "Agent Two", "config": {}},
    )

    assert first.status_code == 200
    assert second.status_code == 429


def test_demo_start_requires_auth_when_demo_bypass_disabled(monkeypatch, client_no_auth: TestClient):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEMO_ALLOW_UNAUTHENTICATED_MUTATIONS", "false")
    get_settings.cache_clear()

    resp = client_no_auth.post(
        "/api/demo/scenarios/ars_submission_showcase/start",
        json={"restart_if_running": True, "speed_multiplier": 1.0},
    )
    assert resp.status_code == 401


def test_demo_start_rate_limited_with_local_bypass(monkeypatch, client_no_auth: TestClient):
    import backend.api.mutation_controls as mutation_controls

    class _StubDirector:
        async def start_scenario(self, *args, **kwargs):
            return {"status": "starting", "scenario": "ars_submission_showcase", "run_id": "demo-1"}

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DEMO_ALLOW_UNAUTHENTICATED_MUTATIONS", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(mutation_controls, "DEMO_SCENARIO_START_LIMIT", 1)
    monkeypatch.setattr(mutation_controls, "RATE_LIMIT_WINDOW_SECONDS", 60.0)

    with patch("backend.api.demo._get_director_from_request", return_value=_StubDirector()):
        first = client_no_auth.post(
            "/api/demo/scenarios/ars_submission_showcase/start",
            json={"restart_if_running": True, "speed_multiplier": 1.0},
        )
        second = client_no_auth.post(
            "/api/demo/scenarios/ars_submission_showcase/start",
            json={"restart_if_running": True, "speed_multiplier": 1.0},
        )

    assert first.status_code == 200
    assert second.status_code == 429
