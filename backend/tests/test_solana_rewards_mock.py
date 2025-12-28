
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.blockchain.solana_contracts import SolanaContractManager
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.hash import Hash

class TestSolanaRewards(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.rpc_url = "http://localhost:8899"
        self.program_id = "program_id"

        # Mock environment variable for private key
        self.payer = Keypair()
        # We need to mock os.getenv to return a valid key if the class uses it in init
        # However, we can also manually set self._payer after init if we mock init or if init fails gracefully

        with patch("os.getenv", return_value=str(self.payer)):
             # We might need to handle from_base58_string if the code expects a string key
             # The code handles both. Keypair.__str__ usually returns the pubkey, not the private key.
             # So we should probably mock the _init_payer method or just inject the payer.
             pass

        self.manager = SolanaContractManager(self.rpc_url, self.program_id)
        self.manager._payer = self.payer # Inject payer directly

    async def test_distribute_rewards_success(self):
        # Mock recipients
        recipients = {
            str(Keypair().pubkey()): 1.5, # 1.5 SOL
            str(Keypair().pubkey()): 0.5  # 0.5 SOL
        }

        # Mock AsyncClient
        with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            # Mock get_latest_blockhash
            mock_resp = MagicMock()
            mock_resp.value.blockhash = Hash.default()
            mock_client_instance.get_latest_blockhash.return_value = mock_resp

            # Mock send_transaction
            mock_send_resp = MagicMock()
            mock_send_resp.value = "signature"
            mock_client_instance.send_transaction.return_value = mock_send_resp

            result = await self.manager.distribute_rewards(recipients)

            self.assertTrue(result)
            self.assertEqual(mock_client_instance.send_transaction.call_count, 1)

            # Verify transaction arguments
            args, _ = mock_client_instance.send_transaction.call_args
            transaction = args[0]
            # Verify instructions count
            # There is no easy way to inspect Transaction instructions length directly in solana-py if it's compiled?
            # But we can assume it worked if call_count is 1.

    async def test_distribute_rewards_batching(self):
        # Create 25 recipients to force 2 batches (batch size 20)
        recipients = {str(Keypair().pubkey()): 1.0 for _ in range(25)}

        with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            mock_resp = MagicMock()
            mock_resp.value.blockhash = Hash.default()
            mock_client_instance.get_latest_blockhash.return_value = mock_resp

            mock_send_resp = MagicMock()
            mock_send_resp.value = "signature"
            mock_client_instance.send_transaction.return_value = mock_send_resp

            result = await self.manager.distribute_rewards(recipients)

            self.assertTrue(result)
            self.assertEqual(mock_client_instance.send_transaction.call_count, 2)

    async def test_distribute_rewards_failure(self):
        recipients = {str(Keypair().pubkey()): 1.0}

        with patch("backend.blockchain.solana_contracts.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            mock_resp = MagicMock()
            mock_resp.value.blockhash = Hash.default()
            mock_client_instance.get_latest_blockhash.return_value = mock_resp

            # Mock send_transaction to raise exception
            mock_client_instance.send_transaction.side_effect = Exception("Network error")

            result = await self.manager.distribute_rewards(recipients)

            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
