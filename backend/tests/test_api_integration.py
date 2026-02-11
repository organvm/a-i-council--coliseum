"""Integration tests for core API MVP flows."""

import pytest
from fastapi.testclient import TestClient

from backend.api import dependencies
from backend.main import app


@pytest.fixture
def client():
    dependencies._orchestrator_instance = None
    with TestClient(app) as test_client:
        yield test_client
    dependencies._orchestrator_instance = None


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_agents_create_and_list(client: TestClient):
    create_resp = client.post(
        "/api/agents/",
        json={"role": "analyst", "name": "Integration Analyst", "config": {}},
    )
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["name"] == "Integration Analyst"
    assert created["role"] == "analyst"

    list_resp = client.get("/api/agents/")
    assert list_resp.status_code == 200
    agents = list_resp.json()
    assert any(a["agent_id"] == created["agent_id"] for a in agents)


def test_events_ingest_and_list_with_source_filter(client: TestClient):
    ingest_resp = client.post(
        "/api/events/ingest",
        json={
            "source": "api",
            "data": {"title": "Policy Update", "description": "new policy"},
            "metadata": {"channel": "news"},
        },
    )
    assert ingest_resp.status_code == 200
    event = ingest_resp.json()
    assert event["source"] == "api"

    list_resp = client.get("/api/events", params={"source": "api", "limit": 10})
    assert list_resp.status_code == 200
    events = list_resp.json()
    assert any(e["event_id"] == event["event_id"] for e in events)


def test_events_invalid_payload_rejected_with_400(client: TestClient):
    resp = client.post(
        "/api/events/ingest",
        json={"source": "api", "data": {"title": "", "description": ""}},
    )
    assert resp.status_code == 400
    assert "Invalid event payload" in resp.json()["detail"]


def test_voting_end_to_end_and_negative_paths(client: TestClient):
    create_resp = client.post(
        "/api/voting/sessions",
        json={
            "title": "Choose direction",
            "description": "direction vote",
            "vote_type": "multiple_choice",
            "options": ["alpha", "beta"],
            "duration_minutes": 60,
            "min_stake": 2.0,
        },
    )
    assert create_resp.status_code == 200
    session_id = create_resp.json()["session_id"]

    missing_resp = client.post(
        "/api/voting/sessions/missing-session/vote",
        json={"user_id": "user_x", "choice": "alpha", "tokens_staked": 2.0},
    )
    assert missing_resp.status_code == 404

    invalid_choice_resp = client.post(
        f"/api/voting/sessions/{session_id}/vote",
        json={"user_id": "user_a", "choice": "gamma", "tokens_staked": 2.0},
    )
    assert invalid_choice_resp.status_code == 400

    insufficient_stake_resp = client.post(
        f"/api/voting/sessions/{session_id}/vote",
        json={"user_id": "user_b", "choice": "alpha", "tokens_staked": 1.0},
    )
    assert insufficient_stake_resp.status_code == 400

    vote_resp = client.post(
        f"/api/voting/sessions/{session_id}/vote",
        json={"user_id": "user_a", "choice": "alpha", "tokens_staked": 2.0},
    )
    assert vote_resp.status_code == 200

    duplicate_vote_resp = client.post(
        f"/api/voting/sessions/{session_id}/vote",
        json={"user_id": "user_a", "choice": "alpha", "tokens_staked": 2.0},
    )
    assert duplicate_vote_resp.status_code == 409

    results_resp = client.get(f"/api/voting/sessions/{session_id}/results")
    assert results_resp.status_code == 200
    assert results_resp.json()["total_votes"] == 1

    inactive_vote_resp = client.post(
        f"/api/voting/sessions/{session_id}/vote",
        json={"user_id": "user_c", "choice": "alpha", "tokens_staked": 2.0},
    )
    assert inactive_vote_resp.status_code == 409

