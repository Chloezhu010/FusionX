#!/usr/bin/env python3
# src/debug_usdc.py
"""
Debug USDC approval issues
"""

import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

def debug_usdc():
    """Debug USDC approval issues"""
    
    print("🔍 Debugging USDC Approval")
    print("=" * 40)
    
    # Load configuration
    eth_rpc_url = os.getenv('ETH_RPC_URL')
    private_key = os.getenv('ETH_PRIVATE_KEY')
    usdc_address = os.getenv('ETH_USDC_ADDRESS')
    
    if not all([eth_rpc_url, private_key, usdc_address]):
        print("❌ Missing environment variables")
        return
    
    try:
        # Setup Web3
        w3 = Web3(Web3.HTTPProvider(eth_rpc_url))
        account = Account.from_key(private_key)
        
        print(f"🔗 Connected to: {eth_rpc_url}")
        print(f"👤 Account: {account.address}")
        print(f"💰 USDC Contract: {usdc_address}")
        
        # Check ETH balance
        eth_balance = w3.eth.get_balance(account.address)
        print(f"\n💰 ETH Balance: {eth_balance / 10**18:.6f} ETH")
        
        # USDC ABI (minimal for balance and allowance)
        usdc_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]
        
        # Create USDC contract instance
        usdc_contract = w3.eth.contract(
            address=w3.to_checksum_address(usdc_address),
            abi=usdc_abi
        )
        
        # Check USDC balance
        try:
            usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
            print(f"💰 USDC Balance: {usdc_balance / 10**6:.6f} USDC")
            print(f"   Raw balance: {usdc_balance} units")
        except Exception as e:
            print(f"❌ Error getting USDC balance: {e}")
            return
        
        # Check current allowance
        escrow_contract = os.getenv('ESCROW_CONTRACT_ADDRESS')
        if escrow_contract:
            try:
                current_allowance = usdc_contract.functions.allowance(
                    account.address, 
                    escrow_contract
                ).call()
                print(f"✅ Current Allowance: {current_allowance / 10**6:.6f} USDC")
                print(f"   Raw allowance: {current_allowance} units")
            except Exception as e:
                print(f"❌ Error getting allowance: {e}")
        
        # Check nonce
        nonce = w3.eth.get_transaction_count(account.address, 'pending')
        print(f"📝 Current nonce: {nonce}")
        
        # Check recent transactions
        print(f"\n📋 Recent transactions:")
        try:
            # Get the latest block
            latest_block = w3.eth.block_number
            # Check last 10 blocks for transactions from this account
            for block_num in range(latest_block - 10, latest_block + 1):
                block = w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    if tx['from'].lower() == account.address.lower():
                        print(f"   Block {block_num}: {tx['hash'].hex()[:20]}... (status: {tx.get('status', 'unknown')}")
        except Exception as e:
            print(f"   Could not check recent transactions: {e}")
        
        # Test approval with small amount
        test_amount = 100000  # 0.1 USDC
        print(f"\n🧪 Testing approval with {test_amount / 10**6:.6f} USDC...")
        
        try:
            # Build approval transaction
            approve_function = usdc_contract.functions.approve(
                escrow_contract,
                test_amount
            )
            
            # Estimate gas
            gas_estimate = approve_function.estimate_gas({'from': account.address})
            print(f"   Estimated gas: {gas_estimate}")
            
            # Get current gas price
            gas_price = w3.eth.gas_price
            print(f"   Current gas price: {gas_price} wei")
            
            # Check if we have enough ETH for gas
            estimated_cost = gas_estimate * gas_price
            if eth_balance < estimated_cost:
                print(f"❌ Insufficient ETH for gas!")
                print(f"   Need: {estimated_cost / 10**18:.6f} ETH")
                print(f"   Have: {eth_balance / 10**18:.6f} ETH")
                return
            
            print(f"✅ Sufficient ETH for gas")
            
        except Exception as e:
            print(f"❌ Error estimating gas: {e}")
            return
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_usdc() 