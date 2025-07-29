#!/usr/bin/env python3
# src/debug_timelock.py
"""
Debug script to check timelock values
"""

import time
import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

def debug_timelock():
    """Debug timelock values"""
    
    print("🔍 Debugging Timelock Values")
    print("=" * 40)
    
    # Current time
    current_time = int(time.time())
    print(f"Current time: {current_time}")
    print(f"Current time (readable): {time.ctime(current_time)}")
    
    # Timelock values from main.py
    src_withdrawal = current_time + 15
    src_cancellation = current_time + 10
    dst_withdrawal = current_time + 15
    dst_cancellation = current_time + 10
    
    print(f"\nTimelock values:")
    print(f"  src_withdrawal: {src_withdrawal} ({time.ctime(src_withdrawal)})")
    print(f"  src_cancellation: {src_cancellation} ({time.ctime(src_cancellation)})")
    print(f"  dst_withdrawal: {dst_withdrawal} ({time.ctime(dst_withdrawal)})")
    print(f"  dst_cancellation: {dst_cancellation} ({time.ctime(dst_cancellation)})")
    
    # Check if we can withdraw now
    can_withdraw = current_time >= src_withdrawal
    can_cancel = current_time >= src_cancellation
    
    print(f"\nCan withdraw now: {can_withdraw}")
    print(f"Can cancel now: {can_cancel}")
    
    if not can_withdraw:
        wait_time = src_withdrawal - current_time
        print(f"Need to wait {wait_time} seconds to withdraw")
    
    # Check contract state if available
    eth_rpc_url = os.getenv('ETH_RPC_URL')
    private_key = os.getenv('ETH_PRIVATE_KEY')
    escrow_contract_address = os.getenv('ESCROW_CONTRACT_ADDRESS')
    
    if all([eth_rpc_url, private_key, escrow_contract_address]):
        try:
            w3 = Web3(Web3.HTTPProvider(eth_rpc_url))
            account = Account.from_key(private_key)
            
            # Try to get the last order hash
            try:
                with open('last_order.txt', 'r') as f:
                    order_hash_hex = f.read().strip()
                    order_hash = bytes.fromhex(order_hash_hex)
                    print(f"\nLast order hash: {order_hash_hex}")
                    
                    # Try to get escrow data from contract
                    # This would require the contract ABI, but for now just show the order hash
                    print(f"Order hash bytes: {order_hash}")
                    
            except FileNotFoundError:
                print("\nNo last_order.txt found")
                
        except Exception as e:
            print(f"Could not connect to contract: {e}")

if __name__ == "__main__":
    debug_timelock() 