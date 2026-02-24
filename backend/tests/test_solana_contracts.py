import pytest
from unittest.mock import MagicMock, patch, AsyncMock

try:
    from backend.blockchain.solana_contracts import SolanaContractManager
    from solders.keypair import Keypair
except Exception as exc:  # pragma: no cover - optional dependency path
    pytest.skip(f"Solana optional dependencies unavailable: {exc}", allow_module_level=True)

@pytest.mark.asyncio
async def test_distribute_rewards_no_payer():
    """Test distribute_rewards returns False when no payer is configured"""
    manager = SolanaContractManager("http://localhost:8899")
    # Ensure no payer
    manager._payer = None

    result = await manager.distribute_rewards({"address": 1.0})
    assert result is False

@pytest.mark.asyncio
async def test_distribute_rewards_success():
    """Test distribute_rewards success path"""
    # Mock AsyncClient
    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        # Setup mock client instance
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance

        # Mock get_latest_blockhash
        mock_blockhash_resp = MagicMock()
        mock_blockhash_resp.value.blockhash = Keypair().pubkey() # Just using a random hash-like object (Pubkey behaves like bytes/hash sometimes) or strictly bytes?
        # Actually blockhash is usually a Hash object or similar.
        # In solana-py 0.30, it is typically solders.hash.Hash
        from solders.hash import Hash
        mock_blockhash_resp.value.blockhash = Hash.default()

        mock_client_instance.get_latest_blockhash.return_value = mock_blockhash_resp

        # Mock send_transaction
        mock_send_resp = MagicMock()
        mock_send_resp.value = "signature"
        mock_client_instance.send_transaction.return_value = mock_send_resp

        manager = SolanaContractManager("http://localhost:8899")
        # Inject a fake payer
        manager._payer = Keypair()

        recipients = {
            str(Keypair().pubkey()): 1.5, # 1.5 SOL
            str(Keypair().pubkey()): 0.5  # 0.5 SOL
        }

        result = await manager.distribute_rewards(recipients)

        assert result is True

        # Verify transaction construction
        # send_transaction(transaction, signer)
        assert mock_client_instance.send_transaction.called
        args, kwargs = mock_client_instance.send_transaction.call_args
        transaction = args[0]
        signer = args[1]

        assert signer == manager._payer
        assert len(transaction.message.instructions) == 2

@pytest.mark.asyncio
async def test_distribute_rewards_invalid_address():
    """Test distribute_rewards handles invalid addresses gracefully"""
    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance

        # Mock blockhash
        from solders.hash import Hash
        mock_blockhash_resp = MagicMock()
        mock_blockhash_resp.value.blockhash = Hash.default()
        mock_client_instance.get_latest_blockhash.return_value = mock_blockhash_resp

        # Mock send response
        mock_send_resp = MagicMock()
        mock_send_resp.value = "signature"
        mock_client_instance.send_transaction.return_value = mock_send_resp

        manager = SolanaContractManager("http://localhost:8899")
        manager._payer = Keypair()

        recipients = {
            "invalid_address": 1.0,
            str(Keypair().pubkey()): 0.5
        }

        result = await manager.distribute_rewards(recipients)

        # Should still succeed for the valid one
        assert result is True

        # Verify only 1 instruction added
        args, kwargs = mock_client_instance.send_transaction.call_args
        transaction = args[0]
        assert len(transaction.message.instructions) == 1
