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
        Stake tokens for governance.

        Currently assumes the user_address matches the configured payer (backend wallet),
        as the backend cannot sign transactions for arbitrary users without their private key.
        The tokens are transferred to the program_id address (simulating a staking vault).
        
        Args:
            user_address: User's Solana address
            amount: Amount to stake (in SOL)
            
        Returns:
            True if successful
        """
        if not self._payer:
            logger.error("No payer configured for staking")
            return False

        # Verify we can sign for this user (custodial/agent mode)
        if user_address != str(self._payer.pubkey()):
            logger.error(f"Cannot stake for address {user_address}. Backend can only sign for {self._payer.pubkey()}")
            return False

        async with AsyncClient(self.rpc_url) as client:
            try:
                # Convert SOL to lamports (1 SOL = 1e9 lamports)
                lamports = int(amount * 1_000_000_000)

                if lamports <= 0:
                    logger.error("Invalid stake amount")
                    return False

                # Destination: Using program_id as the staking vault/contract address
                try:
                    staking_vault = Pubkey.from_string(self.program_id)
                except ValueError:
                    logger.error(f"Invalid program ID (staking vault): {self.program_id}")
                    return False

                ix = transfer(
                    TransferParams(
                        from_pubkey=self._payer.pubkey(),
                        to_pubkey=staking_vault,
                        lamports=lamports
                    )
                )

                # Get recent blockhash
                try:
                    latest_blockhash_resp = await client.get_latest_blockhash()
                    latest_blockhash = latest_blockhash_resp.value.blockhash
                except Exception as e:
                    logger.error(f"Failed to get latest blockhash: {e}")
                    return False

                # Create and sign transaction
                # Transaction.new_signed_with_payer(instructions, payer, signing_keypairs, recent_blockhash)
                transaction = Transaction.new_signed_with_payer(
                    [ix],
                    self._payer.pubkey(),
                    [self._payer],
                    latest_blockhash
                )

                # Send transaction
                try:
                    resp = await client.send_transaction(
                        transaction
                    )
                    logger.info(f"Staked successfully. Signature: {resp.value}")
                    return True

                except Exception as e:
                    logger.error(f"Failed to send transaction: {e}")
                    return False

            except Exception as e:
                logger.error(f"Error executing stake: {e}")
                return False
    
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
                instructions = []

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
                    instructions.append(ix)

                if not instructions:
                    return True

                # Get recent blockhash
                try:
                    latest_blockhash_resp = await client.get_latest_blockhash()
                    latest_blockhash = latest_blockhash_resp.value.blockhash
                except Exception as e:
                    logger.error(f"Failed to get latest blockhash: {e}")
                    return False

                # Create and sign transaction
                transaction = Transaction.new_signed_with_payer(
                    instructions,
                    self._payer.pubkey(),
                    [self._payer],
                    latest_blockhash
                )

                # Send transaction
                try:
                    resp = await client.send_transaction(
                        transaction
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
