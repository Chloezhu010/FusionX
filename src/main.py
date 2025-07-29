# src/main.py
import asyncio
import time
import os
import hashlib
import secrets
from decimal import Decimal
from dotenv import load_dotenv

from eth_manager import EthEscrowManager
from xrpl_usdc_manager import XrplUsdcManager
from usdc_resolver import UsdcCrossChainResolver
from usdc_validator import UsdcSwapValidator
import xrpl

# Load environment variables
load_dotenv()

# Configuration
ETH_RPC_URL = os.getenv('ETH_RPC_URL', 'https://sepolia.infura.io/v3/YOUR_KEY')
ETH_PRIVATE_KEY = os.getenv('ETH_PRIVATE_KEY')
ESCROW_CONTRACT = os.getenv('ESCROW_CONTRACT_ADDRESS')
XRPL_RPC_URL = os.getenv('XRPL_RPC_URL', 'wss://s.altnet.rippletest.net:51233')
XRPL_WALLET_SEED = os.getenv('XRPL_WALLET_SEED')

# USDC Addresses
# Official Sepolia USDC address
# source: https://developers.circle.com/stablecoins/usdc-contract-addresses
ETH_USDC_ADDRESS = os.getenv('ETH_USDC_ADDRESS', '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238')
XRPL_USDC_ISSUER = os.getenv('XRPL_USDC_ISSUER', 'rHuGNhqTG32mfmAvWA8hUyWRLV3tCSwKQt')

def generate_order_hash() -> bytes:
    """Generate unique order hash"""
    timestamp = str(int(time.time()))
    random_bytes = secrets.token_bytes(16)
    return hashlib.sha256((timestamp + random_bytes.hex()).encode()).digest()

def eth_to_xrpl_usdc(eth_amount: int) -> str:
    """Convert ETH USDC amount to XRPL format"""
    return f"{eth_amount / 1000000:.6f}"

def xrpl_to_eth_usdc(xrpl_amount: str) -> int:
    """Convert XRPL USDC amount to ETH format"""
    return int(float(xrpl_amount) * 1000000)

def validate_addresses(eth_addr: str, xrpl_addr: str) -> bool:
    """Validate ETH and XRPL addresses"""
    # ETH: 0x... format, 42 characters
    eth_valid = eth_addr.startswith('0x') and len(eth_addr) == 42
    
    # XRPL: r... format, 25-34 characters
    xrpl_valid = xrpl_addr.startswith('r') and 25 <= len(xrpl_addr) <= 34
    
    return eth_valid and xrpl_valid

async def example_eth_to_xrpl_swap():
    """Example: Swap 100 USDC from ETH to XRPL"""
    
    if not all([ETH_PRIVATE_KEY, ESCROW_CONTRACT, XRPL_WALLET_SEED]):
        print("❌ Missing required environment variables!")
        print("Please set: ETH_PRIVATE_KEY, ESCROW_CONTRACT_ADDRESS, XRPL_WALLET_SEED")
        return
    
    try:
        # Initialize XRPL wallet
        xrpl_wallet = xrpl.wallet.Wallet.from_seed(XRPL_WALLET_SEED)
        print(f"🔑 XRPL Wallet: {xrpl_wallet.address}")
        
        # Initialize managers
        eth_manager = EthEscrowManager(ETH_RPC_URL, ETH_PRIVATE_KEY, ESCROW_CONTRACT)
        xrpl_manager = XrplUsdcManager(XRPL_RPC_URL, xrpl_wallet)
        
        resolver = UsdcCrossChainResolver(eth_manager, xrpl_manager)
        
        # Check balances first
        print("\n💰 Current Balances:")
        print("   (Note: Balance checks may fail on testnets - this is normal)")
        eth_balance = eth_manager.get_account_balance()
        usdc_balance = eth_manager.get_usdc_balance(ETH_USDC_ADDRESS)
        xrpl_usdc_balance = await xrpl_manager.check_usdc_balance(xrpl_wallet.address)
        
        print(f"   ETH: {eth_balance:.4f} ETH")
        print(f"   ETH USDC: {usdc_balance / 1000000:.6f} USDC")
        print(f"   XRPL USDC: {xrpl_usdc_balance} USDC")
        
        if usdc_balance == 0:
            print(f"\n⚠️  Zero USDC balance detected.")
            print(f"   For hackathon/testing: This is normal on testnets.")
            print(f"   The swap demo will still show the complete flow.")
        
        # Create swap order
        order_hash = generate_order_hash()
        current_time = int(time.time())
        
        # Example addresses - using standard test addresses
        example_user = "0x95d94e5370D9C2522dd6a4D7E670f3EC582643b1"  # Valid ETH address (42 chars)
        example_xrpl_user = "rDWVLTo47HuGhrj4Tpdb9gMyZ8gGHrqniv"        # Different XRPL address (34 chars)
        
        if not validate_addresses(example_user, example_xrpl_user):
            print("❌ Invalid example addresses")
            return
        
        # --- Define Swap Amounts ---
        eth_amount_to_swap = 200_000  # 0.2 USDC (6 decimals)
        fee_rate = 0.01  # 1% fee
        xrpl_amount_to_receive = eth_amount_to_swap * (1 - fee_rate)
        xrpl_amount_str = f"{xrpl_amount_to_receive / 1_000_000:.6f}"
        
        swap_order = {
            'order_hash': order_hash,
            'eth_user': example_user,
            'xrpl_user': example_xrpl_user,
            'ETH_USDC_ADDRESS': ETH_USDC_ADDRESS,
            'eth_amount': eth_amount_to_swap,
            'xrpl_amount': xrpl_amount_str,
            'safety_deposit': int(0.01 * 10**18),  # 0.01 ETH safety deposit
            'timelocks': {
                'src_withdrawal': current_time + 15,
                'src_cancellation': current_time + 60,  # Give 1 minute for withdrawal
                'dst_withdrawal': current_time + 15,
                'dst_cancellation': current_time + 10
            }
        }
        
        print(f"\n🚀 Starting USDC swap:")
        print(f"   Order Hash: {order_hash.hex()}")
        print(f"   ETH Amount: {swap_order['eth_amount'] / 1000000} USDC")
        print(f"   XRPL Amount: {swap_order['xrpl_amount']} USDC")
        print(f"   From: {swap_order['eth_user']}")
        print(f"   To: {swap_order['xrpl_user']}")
        
        # --- Step 1: Approve the Escrow Contract to spend USDC ---
        print("\n1️⃣  Approving USDC transfer...")
        try:
            approve_tx = eth_manager.approve_usdc(
                usdc_address=ETH_USDC_ADDRESS,
                spender=ESCROW_CONTRACT,
                amount=swap_order['eth_amount']
            )
            print(f"   Approval transaction sent: {approve_tx}")
        except Exception as e:
            print(f"❌ Approval failed: {e}")
            print("   This can happen if you don't have enough test USDC in your wallet.")
            return
        
        # --- Step 2: Execute the swap ---
        print("\n2️⃣  Executing swap...")
        result = await resolver.execute_usdc_swap(swap_order)
        
        if result['status'] == 'success':
            print("✅ Swap completed successfully!")
            print(f"   ETH Transaction: {result['eth_tx']}")
            print(f"   XRPL Transaction: {result['xrpl_tx']}")
            
            # Store order hash for later use
            with open('last_order.txt', 'w') as f:
                f.write(order_hash.hex())
                
        else:
            print(f"❌ Swap failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Swap execution failed: {e}")
        import traceback
        traceback.print_exc()

async def example_swap_status_check(order_hash: bytes = None):
    """Check status of existing swap"""
    if not order_hash:
        # Try to load from file
        try:
            with open('last_order.txt', 'r') as f:
                order_hash = bytes.fromhex(f.read().strip())
        except FileNotFoundError:
            print("❌ No order hash provided and no last_order.txt found")
            return
    
    if not ESCROW_CONTRACT:
        print("❌ ESCROW_CONTRACT_ADDRESS not set")
        return
    
    eth_manager = EthEscrowManager(ETH_RPC_URL, ETH_PRIVATE_KEY, ESCROW_CONTRACT)
    
    status = eth_manager.get_escrow_status(order_hash)
    print(f"\n📊 Swap Status for {order_hash.hex()}:")
    print(f"   Exists: {status.get('exists', False)}")
    print(f"   Completed: {status.get('completed', False)}")
    
    if status.get('exists'):
        print(f"   Maker: {status.get('maker')}")
        print(f"   Taker: {status.get('taker')}")
        print(f"   Amount: {status.get('amount', 0) / 1000000:.6f} USDC")
        print(f"   XRPL Destination: {status.get('xrpl_destination')}")
        print(f"   XRPL Amount: {status.get('xrpl_amount')}")

async def test_balances():
    """Test USDC balance checking"""
    if not all([ETH_PRIVATE_KEY, XRPL_WALLET_SEED]):
        print("❌ Missing ETH_PRIVATE_KEY or XRPL_WALLET_SEED")
        return
    
    try:
        # Initialize managers
        xrpl_wallet = xrpl.wallet.Wallet.from_seed(XRPL_WALLET_SEED)
        eth_manager = EthEscrowManager(ETH_RPC_URL, ETH_PRIVATE_KEY, ESCROW_CONTRACT or "0x0")
        xrpl_manager = XrplUsdcManager(XRPL_RPC_URL, xrpl_wallet)
        
        print("\n💰 Account Balances:")
        print(f"   ETH Address: {eth_manager.account.address}")
        print(f"   ETH Balance: {eth_manager.get_account_balance():.4f} ETH")
        print(f"   ETH USDC Balance: {eth_manager.get_usdc_balance(ETH_USDC_ADDRESS) / 1000000:.6f} USDC")
        
        print(f"\n   XRPL Address: {xrpl_wallet.address}")
        xrpl_usdc_balance = await xrpl_manager.check_usdc_balance(xrpl_wallet.address)
        print(f"   XRPL USDC Balance: {xrpl_usdc_balance} USDC")
        
    except Exception as e:
        print(f"❌ Balance check failed: {e}")

async def interactive_swap():
    """Interactive swap creation"""
    print("\n🔄 Interactive USDC Swap Creation")
    
    try:
        eth_user = input("Enter ETH user address (0x...): ").strip()
        xrpl_user = input("Enter XRPL user address (r...): ").strip()
        
        if not validate_addresses(eth_user, xrpl_user):
            print("❌ Invalid addresses provided")
            return
        
        eth_amount_str = input("Enter ETH USDC amount (e.g., 100.5): ").strip()
        eth_amount = int(float(eth_amount_str) * 1000000)  # Convert to 6 decimals
        
        fee_rate = float(input("Enter fee rate (e.g., 0.01 for 1%): ").strip())
        xrpl_amount = eth_amount * (1 - fee_rate)
        xrpl_amount_str = f"{xrpl_amount / 1000000:.6f}"
        
        print(f"\n📋 Swap Summary:")
        print(f"   ETH USDC: {eth_amount / 1000000:.6f}")
        print(f"   XRPL USDC: {xrpl_amount_str}")
        print(f"   Fee: {fee_rate * 100:.2f}%")
        
        confirm = input("\nProceed? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Swap cancelled")
            return
        
        # Create and execute swap
        order_hash = generate_order_hash()
        current_time = int(time.time())
        
        swap_order = {
            'order_hash': order_hash,
            'eth_user': eth_user,
            'xrpl_user': xrpl_user,
            'ETH_USDC_ADDRESS': ETH_USDC_ADDRESS,
            'eth_amount': eth_amount,
            'xrpl_amount': xrpl_amount_str,
            'safety_deposit': int(0.01 * 10**18),
            'timelocks': {
                'src_withdrawal': current_time + 15,
                'src_cancellation': current_time + 60,  # Give 1 minute for withdrawal
                'dst_withdrawal': current_time + 15,
                'dst_cancellation': current_time + 10
            }
        }
        
        xrpl_wallet = xrpl.wallet.Wallet.from_seed(XRPL_WALLET_SEED)
        eth_manager = EthEscrowManager(ETH_RPC_URL, ETH_PRIVATE_KEY, ESCROW_CONTRACT)
        xrpl_manager = XrplUsdcManager(XRPL_RPC_URL, xrpl_wallet)
        resolver = UsdcCrossChainResolver(eth_manager, xrpl_manager)
        
        # --- Step 1: Approve the Escrow Contract to spend USDC ---
        print("\n1️⃣  Approving USDC transfer...")
        try:
            approve_tx = eth_manager.approve_usdc(
                usdc_address=ETH_USDC_ADDRESS,
                spender=ESCROW_CONTRACT,
                amount=swap_order['eth_amount']
            )
            print(f"   Approval transaction sent: {approve_tx}")
        except Exception as e:
            print(f"❌ Approval failed: {e}")
            print("   This can happen if you don't have enough test USDC in your wallet.")
            return
        
        # --- Step 2: Execute the swap ---
        print("\n2️⃣  Executing swap...")
        result = await resolver.execute_usdc_swap(swap_order)
        
        if result['status'] == 'success':
            print("✅ Interactive swap completed!")
            with open('last_order.txt', 'w') as f:
                f.write(order_hash.hex())
        else:
            print(f"❌ Interactive swap failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Interactive swap failed: {e}")

def print_configuration():
    """Print current configuration"""
    print("\n⚙️  Current Configuration:")
    print(f"   ETH RPC: {ETH_RPC_URL}")
    print(f"   ETH Private Key: {'✓ Set' if ETH_PRIVATE_KEY else '❌ Not Set'}")
    print(f"   Escrow Contract: {ESCROW_CONTRACT or '❌ Not Set'}")
    print(f"   XRPL RPC: {XRPL_RPC_URL}")
    print(f"   XRPL Wallet Seed: {'✓ Set' if XRPL_WALLET_SEED else '❌ Not Set'}")
    print(f"   ETH USDC Address: {ETH_USDC_ADDRESS}")
    print(f"   XRPL USDC Issuer: {XRPL_USDC_ISSUER}")

async def main():
    """Main function - choose operation"""
    print("🔄 Xinch - Cross-Chain USDC Swaps")
    print("=" * 50)
    
    print_configuration()
    
    print("\nChoose an operation:")
    print("1. Execute example ETH → XRPL swap")
    print("2. Check swap status") 
    print("3. Check balances")
    print("4. Interactive swap creation")
    print("5. Show configuration")
    print("0. Exit")
    
    try:
        choice = input("\nEnter choice (0-5): ").strip()
        
        if choice == '1':
            await example_eth_to_xrpl_swap()
        elif choice == '2':
            order_hash_hex = input("Enter order hash (hex, or press Enter for last): ").strip()
            if order_hash_hex:
                order_hash = bytes.fromhex(order_hash_hex)
                await example_swap_status_check(order_hash)
            else:
                await example_swap_status_check()
        elif choice == '3':
            await test_balances()
        elif choice == '4':
            await interactive_swap()
        elif choice == '5':
            print_configuration()
        elif choice == '0':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting gracefully...")
    finally:
        print("✅ Application finished.")
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            task.cancel()
        
        if tasks:
            group = asyncio.gather(*tasks, return_exceptions=True)
            loop.run_until_complete(group)
        
        loop.close()