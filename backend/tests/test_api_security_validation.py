
import pytest
from unittest.mock import AsyncMock, patch
import os
import sys

# Mock environment variables
os.environ["SOLANA_PAYER_PRIVATE_KEY"] = "1" * 64

# We need to ensure we can import backend.api.dependencies to patch it
# This might require ensuring 'backend' is in python path, which it is if we run from root.
# But we need to patch BEFORE 'backend.main' is imported if 'backend.main' does 'from ... import initialize_orchestrator'

# Patching directly on the module where it is defined
with patch("backend.api.dependencies.initialize_orchestrator", new_callable=AsyncMock):
    from backend.main import app
    from fastapi.testclient import TestClient

client = TestClient(app)

def test_negative_stake_amount():
    response = client.post("/api/blockchain/stake", json={"amount": -100.0, "lock_period_days": 0})
    assert response.status_code == 422
    # Pydantic v2 error messages might vary slightly, but check for key phrases
    assert "greater than 0" in response.json()["detail"][0]["msg"]

def test_negative_transfer_amount():
    # Use valid address length
    valid_addr = "1" * 32
    response = client.post("/api/blockchain/transfer", json={"to_address": valid_addr, "amount": -50.0})
    assert response.status_code == 422
    assert "greater than 0" in response.json()["detail"][0]["msg"]

def test_short_transfer_address():
    response = client.post("/api/blockchain/transfer", json={"to_address": "short", "amount": 10.0})
    assert response.status_code == 422
    assert "at least 32 characters" in response.json()["detail"][0]["msg"]

def test_negative_duration_voting():
    response = client.post("/api/voting/sessions", json={
        "title": "Vote",
        "description": "Desc",
        "vote_type": "binary",
        "options": ["Yes", "No"],
        "duration_minutes": -10
    })
    assert response.status_code == 422
    assert "greater than 0" in response.json()["detail"][0]["msg"]

def test_empty_options_voting():
    response = client.post("/api/voting/sessions", json={
        "title": "Vote",
        "description": "Desc",
        "vote_type": "binary",
        "options": [],
        "duration_minutes": 60
    })
    assert response.status_code == 422
    assert "at least 2 items" in response.json()["detail"][0]["msg"]

def test_invalid_agent_name():
    # Only whitespace
    response = client.post("/api/agents/", json={
        "role": "debater",
        "name": "   ",
        "config": {}
    })
    assert response.status_code == 422
    # Check for pattern mismatch error
    detail = response.json()["detail"][0]
    assert "pattern" in detail["msg"] or "match" in detail["msg"] or "string_pattern_mismatch" in detail["type"]
