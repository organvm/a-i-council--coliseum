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
from solana.transaction import Transaction
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.keypair import Keypair
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
        try:
            # Check if RPC URL is set
            if not self.rpc_url:
                logger.error("RPC URL not configured")
                return False

            async with AsyncClient(self.rpc_url) as client:
                # 1. Check connection
                try:
                    version = await client.get_version()
                    logger.info(f"Connected to Solana cluster: {version.value}")
                except Exception as e:
                    logger.error(f"Failed to connect to Solana cluster: {e}")
                    return False

                # 2. Verify Program ID
                try:
                    program_pubkey = Pubkey.from_string(self.program_id)
                except ValueError:
                    logger.error(f"Invalid program ID format: {self.program_id}")
                    return False

                # 3. Check Program Account
                try:
                    account_info = await client.get_account_info(program_pubkey)
                    if account_info.value is None:
                        logger.error(f"Program account not found: {self.program_id}")
                        return False

                    if not account_info.value.executable:
                        logger.error(f"Account is not executable (not a program): {self.program_id}")
                        return False

                    logger.info(f"Council program verified: {self.program_id}")
                    return True

                except Exception as e:
                    logger.error(f"Failed to verify program account: {e}")
                    return False

        except Exception as e:
            logger.error(f"Error initializing council program: {e}")
            return False
    
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
            recipients: Dict of address -> amount (in SOL or Lamports?)
            Assuming amount is in SOL for now, need to convert to Lamports.
            
        Returns:
            True if successful
        """
        if not self._payer:
            logger.error("No payer configured for reward distribution")
            return False

        if not recipients:
            return True

        async with AsyncClient(self.rpc_url) as client:
            try:
                # Create transaction
                transaction = Transaction()

                # Add transfer instructions for each recipient
                for address, amount in recipients.items():
                    # Convert SOL to lamports (1 SOL = 1e9 lamports)
                    lamports = int(amount * 1_000_000_000)

                    if lamports <= 0:
                        continue

                    try:
                        to_pubkey = Pubkey.from_string(address)
                    except ValueError:
                        logger.error(f"Invalid recipient address: {address}")
                        continue

                    ix = transfer(
                        TransferParams(
                            from_pubkey=self._payer.pubkey(),
                            to_pubkey=to_pubkey,
                            lamports=lamports
                        )
                    )
                    transaction.add(ix)

                # Get recent blockhash
                try:
                    latest_blockhash_resp = await client.get_latest_blockhash()
                    latest_blockhash = latest_blockhash_resp.value.blockhash
                    transaction.recent_blockhash = latest_blockhash
                except Exception as e:
                    logger.error(f"Failed to get latest blockhash: {e}")
                    return False

                # Sign transaction
                # transaction.sign(self._payer) # This might be different in newer solders/solana versions
                # In solana-py 0.30+, we can use `send_transaction` with signers

                # Send transaction
                # We can pass the transaction object and the signer
                try:
                    # In newer solana-py, we might need to compile to message if using VersionedTransaction
                    # But for legacy Transaction:
                    resp = await client.send_transaction(
                        transaction,
                        self._payer
                    )

                    logger.info(f"Rewards distributed successfully. Signature: {resp.value}")
                    return True

                except Exception as e:
                    logger.error(f"Failed to send transaction: {e}")
                    return False

            except Exception as e:
                logger.error(f"Error distributing rewards: {e}")
                return False
    
    def get_program_accounts(self) -> List[SolanaAccount]:
        """Get all program accounts"""
        return list(self.accounts.values())
