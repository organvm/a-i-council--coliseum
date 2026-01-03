"""
Ethereum Contract Manager

Manages interactions with Ethereum smart contracts.
"""

from typing import Dict, Any, Optional
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.eth import AsyncEth
from eth_account import Account
import os

# Minimal ERC-20 ABI for transfer and balance checking
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


class EthereumContractManager:
    """
    Manager for Ethereum smart contract interactions
    Handles cross-chain functionality and Ethereum-based features
    """
    
    def __init__(self, rpc_url: str, contract_address: str):
        self.rpc_url = rpc_url
        self.contract_address = contract_address
        self.w3: Optional[AsyncWeb3] = None
        self._contract = None
    
    async def initialize_contract(self) -> bool:
        """Initialize contract connection"""
        try:
            self.w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc_url))
            if await self.w3.is_connected():
                self.contract_address = self.w3.to_checksum_address(self.contract_address)
                self._contract = self.w3.eth.contract(
                    address=self.contract_address,
                    abi=ERC20_ABI
                )
                return True
            return False
        except Exception as e:
            # In a real app we might log this error
            return False
    
    async def _ensure_initialized(self):
        if not self.w3:
            await self.initialize_contract()
        if not self.w3:
            raise RuntimeError("Could not initialize Web3 connection")

    async def get_token_balance(self, address: str) -> float:
        """Get ERC-20 token balance"""
        await self._ensure_initialized()
        try:
            address = self.w3.to_checksum_address(address)
            # Fetch decimals to normalize
            decimals = await self._contract.functions.decimals().call()
            balance_wei = await self._contract.functions.balanceOf(address).call()
            return balance_wei / (10 ** decimals)
        except Exception:
            return 0.0
    
    async def transfer_tokens(
        self,
        from_address: str,
        to_address: str,
        amount: float,
        private_key: Optional[str] = None
    ) -> str:
        """
        Transfer tokens
        
        Args:
            from_address: Sender address
            to_address: Recipient address
            amount: Amount to transfer (in token units, e.g. 10.5)
            private_key: Private key of the sender. If None, looks for env var based on usage logic
                         or raises ValueError.

        Returns:
            Transaction hash
        """
        await self._ensure_initialized()

        if not private_key:
            # Try to get from environment if not provided
            # This assumes a system-wide wallet if caller doesn't provide one
            # For specific user transfers, private_key MUST be provided
            private_key = os.environ.get("WALLET_PRIVATE_KEY")
            if not private_key:
                raise ValueError("Private key is required for token transfer")

        # Verify from_address matches private key (optional but good safety)
        account = Account.from_key(private_key)
        if account.address.lower() != from_address.lower():
            # Security: Do not leak the private key's address in the error message
            raise ValueError("Private key does not match the provided from_address")

        to_address = self.w3.to_checksum_address(to_address)
        sender_address = self.w3.to_checksum_address(from_address)

        # Get decimals
        decimals = await self._contract.functions.decimals().call()
        amount_wei = int(amount * (10 ** decimals))

        # Build transaction
        # Get nonce
        nonce = await self.w3.eth.get_transaction_count(sender_address)

        # Estimate gas? Or let build_transaction do it?
        # Usually good to estimate gas or set a standard limit for transfer

        tx_data = await self._contract.functions.transfer(
            to_address,
            amount_wei
        ).build_transaction({
            'from': sender_address,
            'nonce': nonce,
            # 'gas': 100000, # Let it estimate or use default
            # 'gasPrice': await self.w3.eth.gas_price # Modern web3 handles this or EIP-1559
        })

        # Sign transaction
        signed_tx = self.w3.eth.account.sign_transaction(tx_data, private_key=private_key)

        # Send transaction
        tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        return self.w3.to_hex(tx_hash)
    
    async def approve_tokens(
        self,
        owner_address: str,
        spender_address: str,
        amount: float
    ) -> str:
        """
        Approve token spending
        
        Returns:
            Transaction hash
        """
        # Placeholder for actual transaction
        return "0x" + "0" * 64
    
    async def bridge_to_solana(
        self,
        amount: float,
        solana_address: str
    ) -> str:
        """
        Bridge tokens from Ethereum to Solana
        
        Args:
            amount: Amount to bridge
            solana_address: Destination Solana address
            
        Returns:
            Transaction hash
        """
        # Placeholder for actual bridge transaction
        return "0x" + "0" * 64
