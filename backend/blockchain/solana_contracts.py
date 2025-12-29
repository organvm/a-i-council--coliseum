"""
Solana Contract Manager

Manages interactions with Solana smart contracts.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from solana.rpc.async_api import AsyncClient
from solders.transaction import Transaction
from solders.message import Message
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.keypair import Keypair
from solders.hash import Hash
from base58 import b58decode

logger = logging.getLogger(__name__)

class SolanaAccount(BaseModel):
    """Solana account information"""
    address: str
    balance: float
    owner: str
    is_initialized: bool = False


class SolanaContractManager:
    """
    Manager for Solana smart contract interactions
    Handles council selection, staking, and reward contracts
    """
    
    def __init__(self, rpc_url: str, program_id: str):
        self.rpc_url = rpc_url
        self.program_id = program_id
        self.accounts: Dict[str, SolanaAccount] = {}

        # Initialize client and payer
        self._payer: Optional[Keypair] = None
        self._init_payer()

    def _init_payer(self):
        """Initialize payer keypair from environment"""
        try:
            private_key = os.getenv("SOLANA_PAYER_PRIVATE_KEY")
            if private_key:
                # Handle base58 string or bytes
                if isinstance(private_key, str):
                    self._payer = Keypair.from_base58_string(private_key)
                else:
                    self._payer = Keypair.from_bytes(private_key)
        except Exception as e:
            logger.warning(f"Failed to initialize Solana payer: {e}")
    
    async def initialize_council_program(self) -> bool:
        """Initialize the council selection program"""
        # Placeholder for actual Solana program initialization
        return True
    
    async def create_council_account(
        self,
        council_id: str,
        num_seats: int
    ) -> str:
        """
        Create a new council account
        
        Args:
            council_id: Unique council identifier
            num_seats: Number of council seats
            
        Returns:
            Account address
        """
        account_address = f"council_{council_id}"
        account = SolanaAccount(
            address=account_address,
            balance=0.0,
            owner=self.program_id,
            is_initialized=True
        )
        self.accounts[account_address] = account
        return account_address
    
    async def get_council_members(self, council_id: str) -> List[str]:
        """Get current council members"""
        # Placeholder - would read from Solana account
        return []
    
    async def update_council_members(
        self,
        council_id: str,
        members: List[str]
    ) -> bool:
        """
        Update council member list
        
        Args:
            council_id: Council identifier
            members: List of member addresses
            
        Returns:
            True if successful
        """
        # Placeholder for actual Solana transaction
        return True
    
    async def stake_tokens(
        self,
        user_address: str,
        amount: float
    ) -> bool:
        """
        Stake tokens for governance
        
        Args:
            user_address: User's Solana address
            amount: Amount to stake
            
        Returns:
            True if successful
        """
        # Placeholder for actual staking transaction
        return True
    
    async def unstake_tokens(
        self,
        user_address: str,
        amount: float
    ) -> bool:
        """
        Unstake tokens
        
        Args:
            user_address: User's Solana address
            amount: Amount to unstake
            
        Returns:
            True if successful
        """
        # Placeholder for actual unstaking transaction
        return True
    
    async def get_stake_balance(self, user_address: str) -> float:
        """Get user's staked token balance"""
        # Placeholder - would read from Solana account
        return 0.0
    
    async def distribute_rewards(
        self,
        recipients: Dict[str, float]
    ) -> bool:
        """
        Distribute rewards to multiple recipients
        
        Args:
            recipients: Dict of address -> amount (in SOL)
            
        Returns:
            True if successful
        """
        if not self._payer:
            logger.error("No payer configured for reward distribution")
            return False

        if not recipients:
            return True

        # Batch processing constant to avoid transaction size limits
        BATCH_SIZE = 10
        recipient_items = list(recipients.items())
        success = True

        async with AsyncClient(self.rpc_url) as client:
            try:
                latest_blockhash_resp = await client.get_latest_blockhash()
                # Ensure we have a Hash object
                # latest_blockhash_resp.value.blockhash is typically a Hash object in newer versions
                # but if it returns a string, we need to convert it.
                # In solana-py >= 0.30, `get_latest_blockhash` returns `GetLatestBlockhashResp`
                # where `.value.blockhash` is a `Hash` object (from solders.hash).
                latest_blockhash = latest_blockhash_resp.value.blockhash

                if isinstance(latest_blockhash, str):
                     # If for some reason it's a string (e.g. mocked or older version compat), convert it
                     latest_blockhash = Hash.from_string(latest_blockhash)

            except Exception as e:
                logger.error(f"Failed to get blockhash: {e}")
                return False

            for i in range(0, len(recipient_items), BATCH_SIZE):
                batch = recipient_items[i:i + BATCH_SIZE]
                instructions = []

                for address, amount in batch:
                    # Convert SOL to lamports (1 SOL = 1e9 lamports)
                    lamports = int(amount * 1_000_000_000)

                    if lamports <= 0:
                        continue

                    try:
                        to_pubkey = Pubkey.from_string(address)
                    except ValueError:
                        logger.error(f"Invalid recipient address: {address}")
                        success = False
                        continue

                    ix = transfer(
                        TransferParams(
                            from_pubkey=self._payer.pubkey(),
                            to_pubkey=to_pubkey,
                            lamports=lamports
                        )
                    )
                    instructions.append(ix)

                if not instructions:
                    continue

                try:
                    msg = Message(instructions, self._payer.pubkey())
                    tx = Transaction.new_unsigned(msg)
                    tx.sign([self._payer], latest_blockhash)

                    resp = await client.send_transaction(tx)
                    logger.info(f"Rewards batch distributed successfully. Signature: {resp.value}")

                except Exception as e:
                    logger.error(f"Failed to send reward batch: {e}")
                    success = False

            return success
    
    def get_program_accounts(self) -> List[SolanaAccount]:
        """Get all program accounts"""
        return list(self.accounts.values())
