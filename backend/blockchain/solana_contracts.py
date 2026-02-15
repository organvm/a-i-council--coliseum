"""
Solana Contract Manager

Manages interactions with Solana smart contracts and balance reading.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

logger = logging.getLogger(__name__)

class SolanaAccount(BaseModel):
    """Solana account information"""
    address: str
    balance: float
    owner: str
    is_initialized: bool = False


class SolanaContractManager:
    """
    Manager for Solana smart contract interactions.
    Handles balance reading and reward distribution logic.
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        self._payer: Optional[Keypair] = None
        self._init_payer()

    def _init_payer(self):
        """Initialize payer keypair from environment"""
        try:
            private_key = os.getenv("SOLANA_PAYER_PRIVATE_KEY")
            if private_key:
                self._payer = Keypair.from_base58_string(private_key)
        except Exception as e:
            logger.warning(f"Failed to initialize Solana payer: {e}")

    async def get_balance(self, address: str) -> float:
        """
        Get SOL balance for an address.
        
        Args:
            address: Solana wallet address
            
        Returns:
            Balance in SOL
        """
        async with AsyncClient(self.rpc_url) as client:
            try:
                pubkey = Pubkey.from_string(address)
                resp = await client.get_balance(pubkey)
                # Convert lamports to SOL
                return resp.value / 1_000_000_000
            except Exception as e:
                logger.error(f"Error reading balance for {address}: {e}")
                return 0.0

    async def get_token_balance(self, address: str, mint_address: str) -> float:
        """
        Get SPL token balance for an address.
        
        Args:
            address: Solana wallet address
            mint_address: SPL Token mint address
            
        Returns:
            Token balance
        """
        async with AsyncClient(self.rpc_url) as client:
            try:
                pubkey = Pubkey.from_string(address)
                mint_pubkey = Pubkey.from_string(mint_address)
                
                # Get token accounts by owner
                resp = await client.get_token_accounts_by_owner_json_parsed(
                    pubkey,
                    {"mint": mint_pubkey}
                )
                
                if not resp.value:
                    return 0.0
                
                # Sum balances if multiple accounts exist (rare but possible)
                total = 0.0
                for account in resp.value:
                    amount = account.account.data.parsed['info']['tokenAmount']['uiAmount']
                    total += float(amount or 0)
                
                return total
            except Exception as e:
                logger.error(f"Error reading token balance for {address}: {e}")
                return 0.0

    async def verify_stake_tier(self, address: str) -> str:
        """
        Determine voter tier based on on-chain token balance.
        
        Example Tiers:
        - BRONZE: < 1 SOL
        - SILVER: 1-10 SOL
        - GOLD: 10-100 SOL
        - PLATINUM: > 100 SOL
        """
        balance = await self.get_balance(address)
        
        if balance >= 100:
            return "PLATINUM"
        if balance >= 10:
            return "GOLD"
        if balance >= 1:
            return "SILVER"
        return "BRONZE"
