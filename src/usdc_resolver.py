# src/usdc_resolver.py
import asyncio
import secrets
import hashlib
from decimal import Decimal
import time
from dotenv import load_dotenv

class UsdcCrossChainResolver:
    def __init__(self, eth_manager, xrpl_manager):
        self.eth_manager = eth_manager
        self.xrpl_manager = xrpl_manager
        self.pending_swaps = {}
    
    async def execute_usdc_swap(self, order: dict) -> dict:
        """Execute ETH USDC -> XRPL USDC swap"""
        try:
            print(f"🔄 Starting USDC swap: {order['eth_amount'] / 1000000} ETH USDC -> {order['xrpl_amount']} XRPL USDC")
            
            # 1. Generate secret for atomic swap
            secret = secrets.token_bytes(32)
            # Use Keccak-256 (same as Solidity keccak256) instead of SHA-256
            from web3 import Web3
            secret_hash_bytes = Web3.keccak(secret)  # This returns bytes32
            secret_hash = secret_hash_bytes.hex()  # Keep the full hex with 0x prefix for proper display
            
            print(f"🔑 Generated secret hash: {secret_hash}")
            print(f"   Secret hash length: {len(secret_hash)} characters")
            print(f"   Secret hash bytes length: {len(secret_hash_bytes)} bytes")
            
            # 2. Deploy Ethereum USDC escrow
            eth_escrow_params = {
                'order_hash': order['order_hash'],
                'hashlock': secret_hash_bytes,  # Use the bytes32 directly
                'maker': order['eth_user'],
                'taker': self.eth_manager.account.address,  # Resolver is the taker
                'xrpl_destination': order['xrpl_user'],
                'usdc_token': order['ETH_USDC_ADDRESS'],
                'amount': order['eth_amount'],  # e.g., 100000000 (100 USDC)
                'safety_deposit': order['safety_deposit'],
                'xrpl_currency': 'USD',
                'xrpl_issuer': self.xrpl_manager.USDC_ISSUER,
                'xrpl_amount': order['xrpl_amount'],  # e.g., "100.000000"
                'timelocks': order['timelocks']
            }
            
            print("📝 Creating ETH escrow...")
            eth_tx = self.eth_manager.create_escrow(eth_escrow_params)
            print(f"✅ ETH escrow created: {eth_tx}")
            
            # 3. Send XRPL USDC to user
            print("💸 Sending XRPL USDC payment...")
            xrpl_tx = await self.xrpl_manager.send_usdc_payment(
                destination=order['xrpl_user'],
                amount=order['xrpl_amount']
            )
            print(f"✅ XRPL USDC payment sent: {xrpl_tx}")
            
            # 4. Store swap state
            order_hash_hex = order['order_hash'].hex()
            self.pending_swaps[order_hash_hex] = {
                'secret': secret,
                'secret_hash': secret_hash,
                'eth_tx': eth_tx,
                'xrpl_tx': xrpl_tx,
                'order': order,
                'eth_escrow_params': eth_escrow_params,
                'status': 'awaiting_user_validation'
            }
            
            print("⏳ Waiting for user validation...")
            
            # 5. Simulate user validation and completion
            # In a real implementation, this would be a separate step triggered by the user
            await self.complete_usdc_swap(order_hash_hex, secret)
            
            return {
                'status': 'success',
                'eth_tx': eth_tx,
                'xrpl_tx': xrpl_tx,
                'order_hash': order_hash_hex
            }
            
        except Exception as e:
            print(f"❌ USDC swap failed: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'failed', 'error': str(e)}
    
    async def complete_usdc_swap(self, order_hash: str, user_secret: bytes):
        """Complete swap after user validation"""
        swap = self.pending_swaps.get(order_hash)
        if not swap:
            raise ValueError("Swap not found")
        
        try:
            print("🔓 Completing swap with user secret...")
            
            # Verify secret matches
            if user_secret != swap['secret']:
                raise ValueError("Invalid secret")
            
            # Check if we need to wait for the withdrawal timelock
            current_time = int(time.time())
            withdrawal_time = swap['order']['timelocks']['src_withdrawal']
            
            if current_time < withdrawal_time:
                wait_seconds = withdrawal_time - current_time
                # Increase wait time to be safely longer than block time
                final_wait = max(wait_seconds, 0) + 35 
                print(f"⏳ Waiting {final_wait} seconds for withdrawal timelock...")
                await asyncio.sleep(final_wait)
                print("✅ Timelock period completed")
            
            # In a real implementation, we would wait for user to reveal secret
            # through XRPL transaction or off-chain communication
            
            # For now, resolver can withdraw ETH USDC using the secret and XRPL tx proof
            print("💰 Withdrawing ETH USDC...")
            eth_withdraw_tx = self.eth_manager.withdraw_escrow(
                secret=user_secret,
                order_hash=swap['order']['order_hash'],
                xrpl_tx_hash=swap['xrpl_tx']
            )
            
            # Update swap status
            swap['status'] = 'completed'
            swap['eth_withdraw_tx'] = eth_withdraw_tx
            
            print(f"✅ Swap completed successfully!")
            print(f"   ETH Withdraw TX: {eth_withdraw_tx}")
            
        except Exception as e:
            print(f"❌ Failed to complete swap: {e}")
            # Optionally, update swap status to 'failed'
            swap['status'] = 'failed'
            raise e
    
    def get_swap_status(self, order_hash: str) -> dict:
        """Get current status of a swap"""
        swap = self.pending_swaps.get(order_hash)
        if not swap:
            return {'status': 'not_found'}
        
        return {
            'status': swap['status'],
            'eth_tx': swap.get('eth_tx'),
            'xrpl_tx': swap.get('xrpl_tx'),
            'eth_withdraw_tx': swap.get('eth_withdraw_tx'),
            'secret_hash': swap.get('secret_hash'),
            'created_at': swap.get('created_at', time.time())
        }
    
    async def wait_for_user_secret(self, order_hash: str, timeout: int = 3600):
        """Wait for user to share secret (placeholder for real implementation)"""
        # In a real implementation, this would:
        # 1. Monitor XRPL for transactions that reveal the secret
        # 2. Wait for off-chain communication from user
        # 3. Validate that user has received XRPL tokens
        
        print(f"⏳ Waiting for user validation for order {order_hash}")
        print("   In production, user would:")
        print("   1. Validate XRPL payment is correct")
        print("   2. Share secret to unlock ETH escrow")
        
        # For demo, just wait a bit
        await asyncio.sleep(5)
        
        swap = self.pending_swaps.get(order_hash)
        if swap:
            # Simulate user sharing secret
            print("✅ User validated XRPL payment and shared secret")
            await self.complete_usdc_swap(order_hash, swap['secret'])
    
    async def cancel_swap(self, order_hash: str) -> dict:
        """Cancel a swap if something goes wrong"""
        swap = self.pending_swaps.get(order_hash)
        if not swap:
            return {'status': 'not_found'}
        
        try:
            print(f"❌ Cancelling swap {order_hash}")
            
            # Cancel ETH escrow if possible (after timeout)
            order_hash_bytes = bytes.fromhex(order_hash)
            cancel_tx = self.eth_manager.cancel_escrow(order_hash_bytes)
            
            swap['status'] = 'cancelled'
            swap['cancel_tx'] = cancel_tx
            
            print(f"✅ Swap cancelled: {cancel_tx}")
            
            return {
                'status': 'cancelled',
                'cancel_tx': cancel_tx
            }
            
        except Exception as e:
            print(f"❌ Failed to cancel swap: {e}")
            return {'status': 'cancel_failed', 'error': str(e)}
    
    def list_pending_swaps(self) -> dict:
        """List all pending swaps"""
        return {
            order_hash: {
                'status': swap['status'],
                'eth_amount': swap['order']['eth_amount'] / 1000000,
                'xrpl_amount': swap['order']['xrpl_amount'],
                'eth_user': swap['order']['eth_user'],
                'xrpl_user': swap['order']['xrpl_user']
            }
            for order_hash, swap in self.pending_swaps.items()
        }