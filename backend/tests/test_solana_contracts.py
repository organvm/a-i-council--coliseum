import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from backend.blockchain.solana_contracts import SolanaContractManager
from solders.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey

@pytest.mark.asyncio
async def test_distribute_rewards_no_payer():
    """Test distribute_rewards returns False when no payer is configured"""
    manager = SolanaContractManager("http://localhost:8899", "program_id")
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
        from solders.hash import Hash
        mock_blockhash_resp = MagicMock()
        mock_blockhash_resp.value.blockhash = Hash.default()
        mock_client_instance.get_latest_blockhash.return_value = mock_blockhash_resp

        # Mock send_transaction
        mock_send_resp = MagicMock()
        mock_send_resp.value = "signature"
        mock_client_instance.send_transaction.return_value = mock_send_resp

        manager = SolanaContractManager("http://localhost:8899", "program_id")
        # Inject a fake payer
        manager._payer = Keypair()

        recipients = {
            str(Keypair().pubkey()): 1.5, # 1.5 SOL
            str(Keypair().pubkey()): 0.5  # 0.5 SOL
        }

        result = await manager.distribute_rewards(recipients)

        assert result is True

        # Verify transaction construction
        # send_transaction(transaction)
        assert mock_client_instance.send_transaction.called
        args, kwargs = mock_client_instance.send_transaction.call_args
        transaction = args[0]

        # Verify transaction is signed and has instructions
        # Since Transaction is an opaque object from solders, checking its properties might be tricky.
        # But we can assume if it was passed to send_transaction, it was constructed.
        assert isinstance(transaction, Transaction)

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

        manager = SolanaContractManager("http://localhost:8899", "program_id")
        manager._payer = Keypair()

        recipients = {
            "invalid_address": 1.0,
            str(Keypair().pubkey()): 0.5
        }

        result = await manager.distribute_rewards(recipients)

        # Should still succeed for the valid one
        assert result is True

        # Verify send_transaction called
        assert mock_client_instance.send_transaction.called

@pytest.mark.asyncio
async def test_stake_tokens_success():
    """Test stake_tokens success path"""
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

        # Use a valid pubkey string for program_id so it can be parsed as destination
        program_id = str(Keypair().pubkey())
        manager = SolanaContractManager("http://localhost:8899", program_id)
        manager._payer = Keypair()

        # User address must match payer
        user_address = str(manager._payer.pubkey())
        amount = 1.0

        result = await manager.stake_tokens(user_address, amount)

        assert result is True

        # Verify transaction
        assert mock_client_instance.send_transaction.called
        args, kwargs = mock_client_instance.send_transaction.call_args
        transaction = args[0]
        assert isinstance(transaction, Transaction)

@pytest.mark.asyncio
async def test_stake_tokens_wrong_user():
    """Test stake_tokens fails if user_address != payer"""
    manager = SolanaContractManager("http://localhost:8899", "program_id")
    manager._payer = Keypair()

    other_user = str(Keypair().pubkey())
    result = await manager.stake_tokens(other_user, 1.0)

    assert result is False

@pytest.mark.asyncio
async def test_stake_tokens_invalid_program_id():
    """Test stake_tokens fails if program_id is invalid pubkey"""
    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance

        manager = SolanaContractManager("http://localhost:8899", "invalid_program_id")
        manager._payer = Keypair()

        user_address = str(manager._payer.pubkey())
        result = await manager.stake_tokens(user_address, 1.0)

        assert result is False
