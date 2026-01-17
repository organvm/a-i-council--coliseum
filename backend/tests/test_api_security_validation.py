import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api.blockchain import router as blockchain_router
from backend.api.voting import router as voting_router

# Create a lightweight app for testing specific routers
app = FastAPI()
app.include_router(blockchain_router, prefix="/api/blockchain")
app.include_router(voting_router, prefix="/api/voting")

client = TestClient(app)

def test_stake_invalid_amount():
    """Test that staking a negative amount is rejected"""
    response = client.post("/api/blockchain/stake", json={"amount": -100, "lock_period_days": 10})
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

def test_stake_zero_amount():
    """Test that staking zero amount is rejected"""
    response = client.post("/api/blockchain/stake", json={"amount": 0, "lock_period_days": 10})
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

def test_transfer_invalid_amount():
    """Test that transferring a negative amount is rejected"""
    response = client.post("/api/blockchain/transfer", json={"to_address": "0x123", "amount": -50})
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

def test_create_voting_session_insufficient_options():
    """Test that creating a voting session with fewer than 2 options is rejected"""
    response = client.post("/api/voting/sessions", json={
        "title": "Test Vote",
        "description": "Description",
        "vote_type": "multiple_choice",
        "options": ["Option 1"],
        "duration_minutes": 60
    })
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

def test_create_voting_session_negative_duration():
    """Test that creating a voting session with negative duration is rejected"""
    response = client.post("/api/voting/sessions", json={
        "title": "Test Vote",
        "description": "Description",
        "vote_type": "multiple_choice",
        "options": ["Option 1", "Option 2"],
        "duration_minutes": -30
    })
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
