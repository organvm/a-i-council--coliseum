
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_stake_validation_negative_amount():
    response = client.post("/api/blockchain/stake", json={
        "amount": -100.0,
        "lock_period_days": 30
    })
    assert response.status_code == 422
    assert "Input should be greater than 0" in response.text or "greater_than" in response.text

def test_stake_validation_valid():
    response = client.post("/api/blockchain/stake", json={
        "amount": 100.0,
        "lock_period_days": 30
    })
    assert response.status_code == 200
    assert response.json()["amount"] == 100.0

def test_transfer_validation_bad_address():
    # Too short address
    response = client.post("/api/blockchain/transfer", json={
        "to_address": "short",
        "amount": 10.0
    })
    assert response.status_code == 422

def test_voting_session_validation_huge_description():
    response = client.post("/api/voting/sessions", json={
        "title": "Valid Title",
        "description": "A" * 2000, # Too long
        "vote_type": "binary",
        "options": ["Yes", "No"],
        "duration_minutes": 60
    })
    assert response.status_code == 422

def test_voting_session_validation_too_many_options():
    response = client.post("/api/voting/sessions", json={
        "title": "Valid Title",
        "description": "Valid Description",
        "vote_type": "multiple_choice",
        "options": ["Option"] * 25, # Max 20
        "duration_minutes": 60
    })
    assert response.status_code == 422
