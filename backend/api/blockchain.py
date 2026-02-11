"""
Blockchain API Router.

Read endpoints are available as in-memory placeholders. Mutating write endpoints
are intentionally disabled until secure key-management is finalized.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class StakeRequest(BaseModel):
    """Request to stake tokens."""

    amount: float
    lock_period_days: int = 0


class TransferRequest(BaseModel):
    """Request to transfer tokens."""

    to_address: str
    amount: float


@router.get("/balance/{address}")
async def get_balance(address: str):
    """Get token balance for address (placeholder read path)."""
    return {"address": address, "balance": 0.0, "source": "placeholder"}


@router.get("/staking/positions")
async def get_staking_positions():
    """Get staking positions (placeholder read path)."""
    return {"positions": [], "source": "placeholder"}


@router.get("/rewards/pending")
async def get_pending_rewards():
    """Get pending rewards (placeholder read path)."""
    return {"pending_rewards": 0.0, "source": "placeholder"}


@router.post("/stake")
async def stake_tokens(request: StakeRequest):
    """Stake tokens (not yet implemented due custody/key-management constraints)."""
    raise HTTPException(
        status_code=501,
        detail="Staking write operations are disabled until secure key-management is implemented",
    )


@router.post("/unstake/{position_id}")
async def unstake_tokens(position_id: str):
    """Unstake tokens (not yet implemented due custody/key-management constraints)."""
    raise HTTPException(
        status_code=501,
        detail="Unstaking write operations are disabled until secure key-management is implemented",
    )


@router.post("/transfer")
async def transfer_tokens(request: TransferRequest):
    """Transfer tokens (not yet implemented due custody/key-management constraints)."""
    raise HTTPException(
        status_code=501,
        detail="Transfer write operations are disabled until secure key-management is implemented",
    )


@router.post("/rewards/claim")
async def claim_rewards():
    """Claim rewards (not yet implemented due custody/key-management constraints)."""
    raise HTTPException(
        status_code=501,
        detail="Claim write operations are disabled until secure key-management is implemented",
    )
