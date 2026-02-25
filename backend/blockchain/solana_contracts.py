"""
Solana Contract Manager

Manages interactions with Solana smart contracts and balance reading.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import base64

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.message import Message as SoldersMessage
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
    BATCH_SIZE = 15 # Maximum instructions per transaction to stay under 1232 bytes

    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        self._payer: Optional[Keypair] = None
        self._init_payer()

    def _init_payer(self) -> None:
        """Initialize payer keypair from environment if available."""
        # Implementation depends on how secrets are managed
        pass

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
                
                ix = transfer(
                    TransferParams(
                        from_pubkey=sender,
                        to_pubkey=vault_address,
                        lamports=lamports
                    )
                )
                
                recent_blockhash_resp = await client.get_latest_blockhash()
                recent_blockhash = recent_blockhash_resp.value.blockhash
                
                # Create unsigned transaction
                message = SoldersMessage.new_with_blockhash(
                    [ix],
                    sender,
                    recent_blockhash
                )
                tx = Transaction.new_unsigned(message)
                
                return base64.b64encode(bytes(tx)).decode('utf-8')
            except Exception as e:
                logger.error(f"Error building stake tx: {e}")
                raise

    async def build_claim_transaction(self, user_address: str, amount: float) -> str:
        """
        Build an unsigned transaction for claiming rewards.
        """
        return await self.build_stake_transaction(user_address, 0.000001)

    async def distribute_rewards(self, reward_map: Dict[str, float]) -> bool:
        """
        Batch distribute rewards to multiple users using parallel processing.
        """
        if not self._payer:
            logger.error("No payer keypair configured for reward distribution")
            return False
            
        async with AsyncClient(self.rpc_url) as client:
            try:
                all_ixs = []
                for address, amount in reward_map.items():
                    try:
                        recipient = Pubkey.from_string(address)
                        lamports = int(amount * 1_000_000_000)
                        all_ixs.append(transfer(
                            TransferParams(
                                from_pubkey=self._payer.pubkey(),
                                to_pubkey=recipient,
                                lamports=lamports
                            )
                        ))
                    except ValueError:
                        continue
                
                if not all_ixs:
                    return False

                # Split into batches
                batches = [all_ixs[i:i + self.BATCH_SIZE] for i in range(0, len(all_ixs), self.BATCH_SIZE)]
                
                recent_blockhash_resp = await client.get_latest_blockhash()
                recent_blockhash = recent_blockhash_resp.value.blockhash
                
                tasks = []
                for batch in batches:
                    message = SoldersMessage.new_with_blockhash(
                        batch,
                        self._payer.pubkey(),
                        recent_blockhash
                    )
                    tx = Transaction.new_signed_with_payer(
                        [], # No additional signers
                        self._payer.pubkey(),
                        [self._payer],
                        recent_blockhash
                    )
                    # Correctly rebuild with batch instructions
                    tx = Transaction.new_signed_with_payer(
                        batch,
                        self._payer.pubkey(),
                        [self._payer],
                        recent_blockhash
                    )
                    tasks.append(client.send_transaction(tx))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        logger.error(f"Reward batch failed: {res}")
                
                return any(not isinstance(r, Exception) for r in results)
            except Exception as e:
                logger.error(f"Error distributing rewards: {e}")
                return False

    async def get_balance(self, address: str) -> float:
        """Get SOL balance for an address."""
        async with AsyncClient(self.rpc_url) as client:
            try:
                pubkey = Pubkey.from_string(address)
                resp = await client.get_balance(pubkey)
                return resp.value / 1_000_000_000
            except Exception as e:
                logger.error(f"Error reading balance for {address}: {e}")
                return 0.0

    async def get_token_balance(self, address: str, mint_address: str) -> float:
        """Get SPL token balance for an address."""
        async with AsyncClient(self.rpc_url) as client:
            try:
                pubkey = Pubkey.from_string(address)
                mint_pubkey = Pubkey.from_string(mint_address)
                resp = await client.get_token_accounts_by_owner_json_parsed(
                    pubkey,
                    {"mint": mint_pubkey}
                )
                if not resp.value:
                    return 0.0
                total = sum(float(acc.account.data.parsed['info']['tokenAmount']['uiAmount'] or 0) for acc in resp.value)
                return total
            except Exception as e:
                logger.error(f"Error reading token balance for {address}: {e}")
                return 0.0

    async def verify_stake_tier(self, address: str) -> str:
        """Determine voter tier based on on-chain token balance."""
        balance = await self.get_balance(address)
        if balance >= 100: return "PLATINUM"
        if balance >= 10: return "GOLD"
        if balance >= 1: return "SILVER"
        return "BRONZE"
