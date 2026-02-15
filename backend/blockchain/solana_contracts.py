"""
Solana Contract Manager

Manages interactions with Solana smart contracts and balance reading.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import base64

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer

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
    Handles balance reading, transaction building, and reward logic.
    """
    
    PROGRAM_ID = "Coli111111111111111111111111111111111111111"

    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        self._payer: Optional[Keypair] = None
        self._init_payer()

    def get_vault_pda(self) -> Pubkey:
        """Derive the vault PDA as defined in the Anchor contract."""
        program_id = Pubkey.from_string(self.PROGRAM_ID)
        pda, _ = Pubkey.find_program_address([b"vault"], program_id)
        return pda

    async def build_stake_transaction(self, user_address: str, amount: float) -> str:
        """
        Build an unsigned transaction for staking SOL.
        Returns base64 encoded transaction message.
        """
        async with AsyncClient(self.rpc_url) as client:
            try:
                sender = Pubkey.from_string(user_address)
                vault_address = self.get_vault_pda()
                
                lamports = int(amount * 1_000_000_000)
                
                # In a real Anchor implementation, we would use anchorpy 
                # to build the 'stake' instruction. For simplicity here, 
                # we maintain the transfer structure but target the PDA.
                ix = transfer(
                    TransferParams(
                        from_pubkey=sender,
                        to_pubkey=vault_address,
                        lamports=lamports
                    )
                )
                
                recent_blockhash_resp = await client.get_latest_blockhash()
                recent_blockhash = recent_blockhash_resp.value.blockhash
                
                tx = Transaction.new_with_payer(
                    [ix],
                    payer=sender
                )
                tx.recent_blockhash = recent_blockhash
                
                # Serialize to bytes then base64
                return base64.b64encode(bytes(tx)).decode('utf-8')
            except Exception as e:
                logger.error(f"Error building stake tx: {e}")
                raise

    async def build_claim_transaction(self, user_address: str, amount: float) -> str:
        """
        Build an unsigned transaction for claiming rewards.
        """
        # Placeholder logic
        return await self.build_stake_transaction(user_address, 0.000001)

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
