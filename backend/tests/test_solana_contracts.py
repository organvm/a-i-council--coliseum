import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.blockchain.solana_contracts import SolanaContractManager
from solders.pubkey import Pubkey

@pytest.mark.asyncio
async def test_initialize_council_program_success():
    # Setup
    rpc_url = "http://localhost:8899"
    program_id = "11111111111111111111111111111111"
    manager = SolanaContractManager(rpc_url, program_id)

    # Mock AsyncClient
    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_client_instance.__aenter__.return_value = mock_client_instance

        # Mock get_version response (successful connection)
        mock_version_resp = MagicMock()
        mock_version_resp.value = {"solana-core": "1.10.0"}
        mock_client_instance.get_version = AsyncMock(return_value=mock_version_resp)

        # Mock get_account_info response (program exists and is executable)
        mock_account_info_resp = MagicMock()
        mock_account_info_resp.value = MagicMock()
        mock_account_info_resp.value.executable = True
        mock_client_instance.get_account_info = AsyncMock(return_value=mock_account_info_resp)

        # Execution
        result = await manager.initialize_council_program()

        # Assertion
        assert result is True
        mock_client_instance.get_version.assert_called_once()
        mock_client_instance.get_account_info.assert_called_once()

@pytest.mark.asyncio
async def test_initialize_council_program_connection_fail():
    # Setup
    rpc_url = "http://localhost:8899"
    program_id = "11111111111111111111111111111111"
    manager = SolanaContractManager(rpc_url, program_id)

    # Mock AsyncClient
    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_client_instance.__aenter__.return_value = mock_client_instance

        # Mock connection failure
        mock_client_instance.get_version = AsyncMock(side_effect=Exception("Connection Refused"))

        # Execution
        result = await manager.initialize_council_program()

        # Assertion
        assert result is False
        mock_client_instance.get_version.assert_called_once()
        # Ensure get_account_info is not called or handle if it's auto-created but not called
        if hasattr(mock_client_instance, 'get_account_info'):
             mock_client_instance.get_account_info.assert_not_called()

@pytest.mark.asyncio
async def test_initialize_council_program_invalid_program_id():
    # Setup
    rpc_url = "http://localhost:8899"
    program_id = "invalid-program-id"
    manager = SolanaContractManager(rpc_url, program_id)

    # Mock AsyncClient
    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_client_instance.__aenter__.return_value = mock_client_instance

        # Mock get_version response
        mock_version_resp = MagicMock()
        mock_version_resp.value = {"solana-core": "1.10.0"}
        mock_client_instance.get_version = AsyncMock(return_value=mock_version_resp)

        # Execution
        result = await manager.initialize_council_program()

        # Assertion
        assert result is False
        mock_client_instance.get_version.assert_called_once()
        if hasattr(mock_client_instance, 'get_account_info'):
            mock_client_instance.get_account_info.assert_not_called()

@pytest.mark.asyncio
async def test_initialize_council_program_not_executable():
    # Setup
    rpc_url = "http://localhost:8899"
    program_id = "11111111111111111111111111111111"
    manager = SolanaContractManager(rpc_url, program_id)

    # Mock AsyncClient
    with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_client_instance.__aenter__.return_value = mock_client_instance

        # Mock get_version response
        mock_version_resp = MagicMock()
        mock_version_resp.value = {"solana-core": "1.10.0"}
        mock_client_instance.get_version = AsyncMock(return_value=mock_version_resp)

        # Mock get_account_info response (account exists but NOT executable)
        mock_account_info_resp = MagicMock()
        mock_account_info_resp.value = MagicMock()
        mock_account_info_resp.value.executable = False
        mock_client_instance.get_account_info = AsyncMock(return_value=mock_account_info_resp)

        # Execution
        result = await manager.initialize_council_program()

        # Assertion
        assert result is False
        mock_client_instance.get_version.assert_called_once()
        mock_client_instance.get_account_info.assert_called_once()
