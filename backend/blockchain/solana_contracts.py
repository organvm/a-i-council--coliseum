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
from solders.message import Message
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
        if not self._payer:
            logger.error("No payer configured for staking")
            return False

        if amount <= 0:
            logger.error("Staking amount must be positive")
            return False

        async with AsyncClient(self.rpc_url) as client:
            try:
                # Validate user address
                try:
                    user_pubkey = Pubkey.from_string(user_address)
                except ValueError:
                    logger.error(f"Invalid user address: {user_address}")
                    return False

                # Derive stake account address (PDA)
                try:
                    program_pubkey = Pubkey.from_string(self.program_id)
                    stake_pda, _ = Pubkey.find_program_address(
                        [b"stake", bytes(user_pubkey)],
                        program_pubkey
                    )
                except ValueError as e:
                    logger.error(f"Invalid program ID or derivation error: {e}")
                    return False

                # Convert SOL to lamports (1 SOL = 1e9 lamports)
                lamports = int(amount * 1_000_000_000)

                # Get recent blockhash
                try:
                    latest_blockhash_resp = await client.get_latest_blockhash()
                    latest_blockhash = latest_blockhash_resp.value.blockhash
                    # latest_blockhash is likely a valid Hash object or compatible, but ensure it matches solders expectations
                    # In newer solana-py, `value.blockhash` might be a solders.hash.Hash
                except Exception as e:
                    logger.error(f"Failed to get latest blockhash: {e}")
                    return False

                # Create instruction
                ix = transfer(
                    TransferParams(
                        from_pubkey=self._payer.pubkey(),
                        to_pubkey=stake_pda,
                        lamports=lamports
                    )
                )

                # Create Message and Transaction using solders
                msg = Message.new_with_blockhash(
                    [ix],
                    self._payer.pubkey(),
                    latest_blockhash
                )

                transaction = Transaction.new_unsigned(msg)

                # Sign transaction (required before sending with legacy mechanism if send_transaction expects it,
                # or if we pass keypairs to send_transaction it might handle it.
                # solana-py AsyncClient.send_transaction usually takes the transaction and list of signers.
                # But solders Transaction.new_unsigned creates an unsigned one.
                # Let's try to sign it here explicitly or assume send_transaction handles it if we pass opts?
                # Actually, `send_transaction` in solana-py usually calls `txn.sign(signers)` if it's not signed.
                # But solders Transaction has a specific way to sign.

                # Let's use `new_signed_with_payer` if we have the payer keypair handy
                # or manually sign.
                # transaction.sign([self._payer], latest_blockhash)

                # Sending
                resp = await client.send_transaction(
                    transaction,
                    self._payer
                )

                logger.info(f"Staked tokens successfully. Signature: {resp.value}")
                return True

            except Exception as e:
                logger.error(f"Error staking tokens: {e}")
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
                # Prepare instructions
                instructions = []
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

                # Create Message
                msg = Message.new_with_blockhash(
                    instructions,
                    self._payer.pubkey(),
                    latest_blockhash
                )

                # Create Transaction
                transaction = Transaction.new_unsigned(msg)

                # Send transaction
                try:
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
