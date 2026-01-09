import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app=app)

def test_stake_validation():
    # Negative amount
    response = client.post("/api/blockchain/stake", json={"amount": -10, "lock_period_days": 10})
    assert response.status_code == 422

    # Zero amount
    response = client.post("/api/blockchain/stake", json={"amount": 0, "lock_period_days": 10})
    assert response.status_code == 422

    # Negative lock period
    response = client.post("/api/blockchain/stake", json={"amount": 10, "lock_period_days": -5})
    assert response.status_code == 422

    # Valid
    response = client.post("/api/blockchain/stake", json={"amount": 10, "lock_period_days": 10})
    assert response.status_code == 200

def test_transfer_validation():
    # Empty address
    response = client.post("/api/blockchain/transfer", json={"to_address": "", "amount": 10})
    assert response.status_code == 422

    # Short address
    response = client.post("/api/blockchain/transfer", json={"to_address": "short", "amount": 10})
    assert response.status_code == 422

    # Negative amount
    response = client.post("/api/blockchain/transfer", json={"to_address": "0x12345678901234567890", "amount": -5})
    assert response.status_code == 422

    # Valid
    response = client.post("/api/blockchain/transfer", json={"to_address": "0x12345678901234567890", "amount": 10})
    assert response.status_code == 200

def test_voting_validation():
    # Empty title
    response = client.post("/api/voting/sessions", json={
        "title": "",
        "description": "desc",
        "vote_type": "binary",
        "options": ["yes", "no"],
        "duration_minutes": 60
    })
    assert response.status_code == 422

    # Short options list
    response = client.post("/api/voting/sessions", json={
        "title": "Title",
        "description": "desc",
        "vote_type": "binary",
        "options": ["yes"],
        "duration_minutes": 60
    })
    assert response.status_code == 422

    # Negative duration
    response = client.post("/api/voting/sessions", json={
        "title": "Title",
        "description": "desc",
        "vote_type": "binary",
        "options": ["yes", "no"],
        "duration_minutes": -5
    })
    assert response.status_code == 422
