from fastapi.testclient import TestClient
from backend.main import app
from backend.api.dependencies import get_orchestrator
from unittest.mock import MagicMock
import pytest

client = TestClient(app)

# Mock Orchestrator
mock_orchestrator = MagicMock()
mock_orchestrator.agents = {}
mock_orchestrator.add_agent = MagicMock()

def override_get_orchestrator():
    return mock_orchestrator

app.dependency_overrides[get_orchestrator] = override_get_orchestrator

def test_create_agent_validation():
    # 1. Test empty name
    response = client.post(
        "/api/agents/",
        json={"role": "debater", "name": "", "config": {}}
    )
    # Expect 422 Unprocessable Entity
    assert response.status_code == 422, f"Expected 422 for empty name, got {response.status_code}"

    # 2. Test whitespace name
    response = client.post(
        "/api/agents/",
        json={"role": "debater", "name": "   ", "config": {}}
    )
    # Expect 422 Unprocessable Entity
    assert response.status_code == 422, f"Expected 422 for whitespace name, got {response.status_code}"

    # 3. Test name too long (>50 chars)
    long_name = "a" * 51
    response = client.post(
        "/api/agents/",
        json={"role": "debater", "name": long_name, "config": {}}
    )
    # Expect 422 Unprocessable Entity
    assert response.status_code == 422, f"Expected 422 for long name, got {response.status_code}"

    # 4. Test valid name
    response = client.post(
        "/api/agents/",
        json={"role": "debater", "name": "ValidName", "config": {}}
    )
    # Expect 200 OK
    assert response.status_code == 200, f"Expected 200 for valid name, got {response.status_code}: {response.text}"
