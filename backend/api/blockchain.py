"""
Blockchain API Router.

Provides endpoints for reading on-chain state and building unsigned transactions
for staking and rewards. The backend does NOT hold user private keys.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..blockchain.solana_contracts import SolanaContractManager
from .auth import get_current_user
from ..models import User

router = APIRouter()


class StakeRequest(BaseModel):
    """Request to stake tokens."""
    amount: float
    lock_period_days: int = 0


class UnsignedTxResponse(BaseModel):
    """Response containing base64 encoded unsigned transaction."""
    transaction: str
    message: str


@router.get("/balance/{address}")
async def get_balance(address: str):
    """Get real on-chain token balance."""
    manager = SolanaContractManager()
    balance = await manager.get_balance(address)
    return {"address": address, "balance": balance, "source": "mainnet-beta"}


@router.post("/stake", response_model=UnsignedTxResponse)
async def build_stake_tx(
    request: StakeRequest,
    current_user: User = Depends(get_current_user)
):
    """Build an unsigned staking transaction for the user to sign."""
    if not current_user.solana_address:
        raise HTTPException(status_code=400, detail="User wallet not linked")
    
    manager = SolanaContractManager()
    try:
        tx_b64 = await manager.build_stake_transaction(
            current_user.solana_address, 
            request.amount
        )
        return {
            "transaction": tx_b64,
            "message": "Sign this transaction to stake tokens"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rewards/claim", response_model=UnsignedTxResponse)
async def build_claim_tx(
    current_user: User = Depends(get_current_user)
):
    """Build an unsigned claim transaction."""
    if not current_user.solana_address:
        raise HTTPException(status_code=400, detail="User wallet not linked")
        
    manager = SolanaContractManager()
    try:
        tx_b64 = await manager.build_claim_transaction(
            current_user.solana_address,
            0.0 # Amount would be calculated from db rewards
        )
        return {
            "transaction": tx_b64,
            "message": "Sign this transaction to claim rewards"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
