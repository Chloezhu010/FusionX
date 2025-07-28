# tests/test_usdc_swap.py
import pytest
import asyncio
import time
import hashlib
import secrets
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.usdc_resolver import UsdcCrossChainResolver
from src.xrpl_usdc_manager import XrplUsdcManager
from src.eth_manager import EthEscrowManager

class TestUsdcSwap:
    
    @pytest.fixture
    def mock_eth_manager(self):
        manager = Mock(spec=EthEscrowManager)
        manager.create_escrow.return_value = "0x123abc456def789"
        manager.withdraw_escrow.return_value = "0x456def789abc123"
        manager.cancel_escrow.return_value = "0x789abc123def456"
        manager.get_escrow_status.return_value = {
            'exists': True,
            'completed': False,
            'maker': '0x742d35Cc6634C0532925a3b8D0C0c0002e0Fd4f25',
            'taker': '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC',
            'amount': 100000000,
            'xrpl_destination': 'rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH',
            'xrpl_amount': '99.000000'
        }
        manager.account = Mock()
        manager.account.address = '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC'
        return manager
    
    @pytest.fixture 
    def mock_xrpl_manager(self):
        manager = Mock(spec=XrplUsdcManager)
        manager.send_usdc_payment.return_value = "ABC123DEF456789XYZ"
        manager.verify_usdc_payment.return_value = True
        manager.check_usdc_balance.return_value = "100.000000"
        manager.USDC_ISSUER = "rcEGREd5YGXK2grCkeSNRZm2Diq1Hp5jk"
        return manager
    
    @pytest.fixture
    def resolver(self, mock_eth_manager, mock_xrpl_manager):
        return UsdcCrossChainResolver(mock_eth_manager, mock_xrpl_manager)
    
    @pytest.fixture
    def sample_order(self):
        order_hash = hashlib.sha256(b"test_order_" + secrets.token_bytes(16)).digest()
        current_time = int(time.time())
        
        return {
            'order_hash': order_hash,
            'eth_user': '0x742d35Cc6634C0532925a3b8D0C0c0002e0Fd4f25',
            'xrpl_user': 'rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH',
            'eth_amount': 100_000_000,  # 100 USDC
            'xrpl_amount': '99.000000', # 99 USDC
            'safety_deposit': int(0.01 * 10**18),  # 0.01 ETH
            'timelocks': {
                'src_withdrawal': current_time + 600,     # 10 minutes
                'src_cancellation': current_time + 7200,  # 2 hours
                'dst_withdrawal': current_time + 300,     # 5 minutes
                'dst_cancellation': current_time + 3600   # 1 hour
            }
        }
    
    @pytest.mark.asyncio
    async def test_execute_usdc_swap_success(self, resolver, sample_order):
        """Test successful USDC swap execution"""
        result = await resolver.execute_usdc_swap(sample_order)
        
        assert result['status'] == 'success'
        assert 'eth_tx' in result
        assert 'xrpl_tx' in result
        assert 'order_hash' in result
        
        # Verify ETH escrow was created
        resolver.eth_manager.create_escrow.assert_called_once()
        
        # Verify XRPL payment was sent
        resolver.xrpl_manager.send_usdc_payment.assert_called_once()
        
        # Verify swap is stored
        order_hash_hex = sample_order['order_hash'].hex()
        assert order_hash_hex in resolver.pending_swaps
        
        swap_state = resolver.pending_swaps[order_hash_hex]
        assert swap_state['status'] == 'completed'
        assert 'secret' in swap_state
        assert 'secret_hash' in swap_state
    
    @pytest.mark.asyncio
    async def test_complete_usdc_swap_success(self, resolver, sample_order):
        """Test successful swap completion"""
        # First execute the swap
        result = await resolver.execute_usdc_swap(sample_order)
        
        # Get the stored secret
        order_hash_hex = result['order_hash']
        swap_state = resolver.pending_swaps[order_hash_hex]
        user_secret = swap_state['secret']
        
        # Test completion (it should already be completed from execute_usdc_swap)
        assert swap_state['status'] == 'completed'
        assert 'eth_withdraw_tx' in swap_state
    
    @pytest.mark.asyncio
    async def test_invalid_secret_rejection(self, resolver, sample_order):
        """Test that invalid secret is rejected"""
        # Execute swap first
        result = await resolver.execute_usdc_swap(sample_order)
        order_hash_hex = result['order_hash']
        
        # Reset the swap to incomplete state for testing
        resolver.pending_swaps[order_hash_hex]['status'] = 'awaiting_user_validation'
        
        invalid_secret = secrets.token_bytes(32)  # Different secret
        
        with pytest.raises(ValueError, match="Invalid secret"):
            await resolver.complete_usdc_swap(order_hash_hex, invalid_secret)
    
    def test_get_swap_status_existing(self, resolver, sample_order):
        """Test getting status of existing swap"""
        order_hash_hex = sample_order['order_hash'].hex()
        
        # Add a mock swap
        resolver.pending_swaps[order_hash_hex] = {
            'status': 'awaiting_user_validation',
            'eth_tx': '0x123abc456def789',
            'xrpl_tx': 'ABC123DEF456789XYZ',
            'secret_hash': 'abc123def456789',
            'created_at': time.time()
        }
        
        status = resolver.get_swap_status(order_hash_hex)
        
        assert status['status'] == 'awaiting_user_validation'
        assert status['eth_tx'] == '0x123abc456def789'
        assert status['xrpl_tx'] == 'ABC123DEF456789XYZ'
        assert 'created_at' in status
    
    def test_get_swap_status_nonexistent(self, resolver):
        """Test getting status of non-existent swap"""
        status = resolver.get_swap_status('nonexistent_hash')
        assert status['status'] == 'not_found'
    
    @pytest.mark.asyncio
    async def test_cancel_swap_success(self, resolver, sample_order):
        """Test successful swap cancellation"""
        # First create a swap
        await resolver.execute_usdc_swap(sample_order)
        order_hash_hex = sample_order['order_hash'].hex()
        
        # Cancel it
        result = await resolver.cancel_swap(order_hash_hex)
        
        assert result['status'] == 'cancelled'
        assert 'cancel_tx' in result
        
        # Verify cancel_escrow was called
        resolver.eth_manager.cancel_escrow.assert_called_once()
        
        # Verify swap status is updated
        swap_state = resolver.pending_swaps[order_hash_hex]
        assert swap_state['status'] == 'cancelled'
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_swap(self, resolver):
        """Test cancelling non-existent swap"""
        result = await resolver.cancel_swap('nonexistent_hash')
        assert result['status'] == 'not_found'
    
    def test_list_pending_swaps(self, resolver, sample_order):
        """Test listing pending swaps"""
        order_hash_hex = sample_order['order_hash'].hex()
        
        # Add a mock swap
        resolver.pending_swaps[order_hash_hex] = {
            'status': 'awaiting_user_validation',
            'order': sample_order
        }
        
        pending = resolver.list_pending_swaps()
        
        assert order_hash_hex in pending
        swap_info = pending[order_hash_hex]
        assert swap_info['status'] == 'awaiting_user_validation'
        assert swap_info['eth_amount'] == 100.0  # 100 USDC
        assert swap_info['xrpl_amount'] == '99.000000'
        assert swap_info['eth_user'] == sample_order['eth_user']
        assert swap_info['xrpl_user'] == sample_order['xrpl_user']

class TestXrplUsdcManager:
    
    @pytest.fixture
    def mock_xrpl_wallet(self):
        wallet = Mock()
        wallet.address = "rTestWalletAddress123456789"
        return wallet
    
    @pytest.fixture  
    def mock_xrpl_client(self):
        client = Mock()
        # Mock successful payment response
        response = Mock()
        response.result = {'hash': 'ABC123DEF456789XYZ', 'validated': True}
        client.request.return_value = response
        return client
    
    @pytest.fixture
    def xrpl_manager(self, mock_xrpl_wallet, mock_xrpl_client):
        with patch('xrpl.clients.JsonRpcClient', return_value=mock_xrpl_client):
            manager = XrplUsdcManager("wss://test.example.com", mock_xrpl_wallet)
            manager.client = mock_xrpl_client
            return manager
    
    def test_format_usdc_amount(self, xrpl_manager):
        """Test USDC amount formatting"""
        # 1 USDC (1000000 units with 6 decimals)
        assert xrpl_manager._format_usdc_amount(1000000) == "1.000000"
        
        # 100.5 USDC
        assert xrpl_manager._format_usdc_amount(100500000) == "100.500000"
        
        # 0.1 USDC
        assert xrpl_manager._format_usdc_amount(100000) == "0.100000"

class TestEthEscrowManager:
    
    @pytest.fixture
    def mock_web3(self):
        w3 = Mock()
        w3.eth.get_balance.return_value = 1000000000000000000  # 1 ETH
        w3.eth.gas_price = 20000000000  # 20 gwei
        w3.eth.get_transaction_count.return_value = 42
        w3.from_wei.return_value = 1.0
        w3.to_checksum_address = lambda x: x
        
        # Mock contract
        contract = Mock()
        contract.functions.getEscrow.return_value.call.return_value = [
            b'test_order_hash_123456789012',  # orderHash
            b'test_hashlock_123456789012',    # hashlock
            '0x742d35Cc6634C0532925a3b8D0C0c0002e0Fd4f25',  # maker
            '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC',    # taker
            'rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH',             # xrplDestination
            '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',    # usdcToken
            100000000,  # amount
            10000000000000000,  # safetyDeposit
            'USD',      # xrplCurrency
            'rcEGREd5YGXK2grCkeSNRZm2Diq1Hp5jk',  # xrplIssuer
            '99.000000', # xrplAmount
            (1000, 2000, 500, 1500)  # timelocks tuple
        ]
        contract.functions.isCompleted.return_value.call.return_value = False
        w3.eth.contract.return_value = contract
        
        return w3
    
    @pytest.fixture
    def mock_account(self):
        account = Mock()
        account.address = '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC'
        account.key = b'test_private_key'
        return account
    
    @pytest.fixture
    def eth_manager(self, mock_web3, mock_account):
        # Patch Web3 and Account where they are used (in src.eth_manager)
        with patch('src.eth_manager.Web3') as mock_web3_class, \
             patch('src.eth_manager.Account') as mock_account_class:
            
            # Configure our mocks to behave as needed
            mock_web3_class.HTTPProvider.return_value = Mock()
            mock_web3_class.return_value = mock_web3
            mock_account_class.from_key.return_value = mock_account

            manager = EthEscrowManager(
                "https://test.example.com",
                "0xtest_private_key",
                "0xtest_contract_address"
            )
            return manager
    
    def test_get_escrow_status(self, eth_manager):
        """Test getting escrow status"""
        order_hash = b'test_order_hash_123456789012'
        
        status = eth_manager.get_escrow_status(order_hash)
        
        assert status['exists'] == True
        assert status['completed'] == False
        assert status['maker'] == '0x742d35Cc6634C0532925a3b8D0C0c0002e0Fd4f25'
        assert status['amount'] == 100000000
        assert status['xrpl_destination'] == 'rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH'
    
    def test_get_account_balance(self, eth_manager):
        """Test getting ETH account balance"""
        balance = eth_manager.get_account_balance()
        assert balance == 1.0  # 1 ETH

# Integration test
class TestIntegration:
    
    @pytest.mark.asyncio
    async def test_full_swap_flow_mocked(self):
        """Test complete swap flow with mocked components"""
        
        # Create mocked managers
        eth_manager = Mock(spec=EthEscrowManager)
        eth_manager.create_escrow.return_value = "0xeth_tx_hash"
        eth_manager.withdraw_escrow.return_value = "0xeth_withdraw_hash"
        eth_manager.account = Mock()
        eth_manager.account.address = "0xresolver_address"
        
        xrpl_manager = Mock(spec=XrplUsdcManager)
        xrpl_manager.send_usdc_payment.return_value = "xrpl_payment_hash"
        xrpl_manager.USDC_ISSUER = "rcEGREd5YGXK2grCkeSNRZm2Diq1Hp5jk"
        
        resolver = UsdcCrossChainResolver(eth_manager, xrpl_manager)
        
        # Create test order
        order_hash = hashlib.sha256(b"integration_test").digest()
        order = {
            'order_hash': order_hash,
            'eth_user': '0x1234567890123456789012345678901234567890',
            'xrpl_user': 'rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH',
            'eth_amount': 100_000_000,
            'xrpl_amount': '99.000000',
            'safety_deposit': int(0.01 * 10**18),
            'timelocks': {
                'src_withdrawal': int(time.time()) + 600,
                'src_cancellation': int(time.time()) + 7200,
                'dst_withdrawal': int(time.time()) + 300,
                'dst_cancellation': int(time.time()) + 3600
            }
        }
        
        # Execute swap
        result = await resolver.execute_usdc_swap(order)
        
        # Verify result
        assert result['status'] == 'success'
        assert result['eth_tx'] == "0xeth_tx_hash"
        assert result['xrpl_tx'] == "xrpl_payment_hash"
        
        # Verify manager calls
        eth_manager.create_escrow.assert_called_once()
        xrpl_manager.send_usdc_payment.assert_called_once()
        eth_manager.withdraw_escrow.assert_called_once()
        
        # Verify swap state
        order_hash_hex = order_hash.hex()
        assert order_hash_hex in resolver.pending_swaps
        swap_state = resolver.pending_swaps[order_hash_hex]
        assert swap_state['status'] == 'completed'

# Run with: python -m pytest tests/test_usdc_swap.py -v 