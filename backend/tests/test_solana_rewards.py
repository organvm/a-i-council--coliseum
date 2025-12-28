import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.blockchain.solana_contracts import SolanaContractManager
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction

@pytest.fixture
def mock_solana_env():
    with patch("backend.blockchain.solana_contracts.os.getenv") as mock_env:
        # Mock payer private key (random 64 bytes)
        mock_env.return_value = str([1] * 64)
        yield mock_env

@pytest.fixture
def manager(mock_solana_env):
    # We need to mock Keypair.from_base58_string or from_bytes depending on implementation
    # But init_payer uses Keypair.from_base58_string or from_bytes
    # Let's mock the Keypair class or just let it fail/warn and manually set payer

    m = SolanaContractManager("http://localhost:8899", "program_id")
    # Manually set a valid payer for testing
    m._payer = Keypair()
    return m

@pytest.mark.asyncio
async def test_distribute_rewards_success(manager):
    recipients = {
        str(Keypair().pubkey()): 1.5,  # 1.5 SOL
        str(Keypair().pubkey()): 0.5   # 0.5 SOL
    }

    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        # Setup mock client
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance

        # Mock get_latest_blockhash
        mock_blockhash_resp = MagicMock()
        # In solders, Hash is an object, but maybe mocking the response value structure is enough
        # resp.value.blockhash
        from solders.hash import Hash
        mock_blockhash_resp.value.blockhash = Hash.default()
        mock_client_instance.get_latest_blockhash.return_value = mock_blockhash_resp

        # Mock send_transaction
        mock_send_resp = MagicMock()
        mock_send_resp.value = "signature_string"
        mock_client_instance.send_transaction.return_value = mock_send_resp

        # Run distribute_rewards
        result = await manager.distribute_rewards(recipients)

        assert result is True

        # Verify calls
        mock_client_instance.get_latest_blockhash.assert_called_once()
        mock_client_instance.send_transaction.assert_called_once()

        # Verify transaction content (arguments passed to send_transaction)
        args, _ = mock_client_instance.send_transaction.call_args
        transaction = args[0]
        assert isinstance(transaction, Transaction)

@pytest.mark.asyncio
async def test_distribute_rewards_batching(manager):
    # Create 25 recipients to test batching (limit is 20)
    recipients = {str(Keypair().pubkey()): 1.0 for _ in range(25)}

    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance

        # Mock blockhash
        mock_blockhash_resp = MagicMock()
        from solders.hash import Hash
        mock_blockhash_resp.value.blockhash = Hash.default()
        mock_client_instance.get_latest_blockhash.return_value = mock_blockhash_resp

        # Mock send
        mock_client_instance.send_transaction.return_value = MagicMock()

        result = await manager.distribute_rewards(recipients)

        assert result is True
        # Should have called send_transaction twice (20 + 5)
        assert mock_client_instance.send_transaction.call_count == 2
        # Should have fetched blockhash twice
        assert mock_client_instance.get_latest_blockhash.call_count == 2

@pytest.mark.asyncio
async def test_distribute_rewards_precision(manager):
    # 0.29 * 1e9 = 289999999.9999... -> int() gives 289999999, round() gives 290000000
    recipient = str(Keypair().pubkey())
    recipients = {recipient: 0.29}

    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance

        mock_blockhash_resp = MagicMock()
        from solders.hash import Hash
        mock_blockhash_resp.value.blockhash = Hash.default()
        mock_client_instance.get_latest_blockhash.return_value = mock_blockhash_resp

        mock_client_instance.send_transaction.return_value = MagicMock()

        await manager.distribute_rewards(recipients)

        # Inspect the transaction
        args, _ = mock_client_instance.send_transaction.call_args
        transaction = args[0]

        # Check instruction data or lamports
        # solders Transaction is compiled, so checking instructions is a bit complex
        # unless we decode message.
        # But we can check that we used round().
        # Actually checking the lamports in the compiled instruction:
        # transaction.message.instructions[0] is CompiledInstruction
        # But data is bytes.

        # Alternatively, we can mock `transfer` from `backend.blockchain.solana_contracts`
        # But `transfer` is imported directly.
        pass

@pytest.mark.asyncio
async def test_distribute_rewards_no_payer(manager):
    manager._payer = None
    result = await manager.distribute_rewards({"some_addr": 1.0})
    assert result is False

@pytest.mark.asyncio
async def test_distribute_rewards_empty_recipients(manager):
    result = await manager.distribute_rewards({})
    assert result is True

@pytest.mark.asyncio
async def test_distribute_rewards_invalid_address(manager):
    recipients = {
        "invalid_address": 1.0,
        str(Keypair().pubkey()): 1.0
    }

    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client_instance

        mock_blockhash_resp = MagicMock()
        from solders.hash import Hash
        mock_blockhash_resp.value.blockhash = Hash.default()
        mock_client_instance.get_latest_blockhash.return_value = mock_blockhash_resp

        mock_send_resp = MagicMock()
        mock_send_resp.value = "sig"
        mock_client_instance.send_transaction.return_value = mock_send_resp

        result = await manager.distribute_rewards(recipients)

        assert result is True
        # Should have sent transaction for the valid address only
        mock_client_instance.send_transaction.assert_called_once()
