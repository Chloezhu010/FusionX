#!/usr/bin/env python3
# src/test_withdraw.py
"""
Test script to debug the withdraw function
"""

import os
import json
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

def test_withdraw():
    """Test the withdraw function directly"""
    
    print("🧪 Testing Withdraw Function")
    print("=" * 40)
    
    # Load configuration
    eth_rpc_url = os.getenv('ETH_RPC_URL')
    private_key = os.getenv('ETH_PRIVATE_KEY')
    escrow_contract_address = os.getenv('ESCROW_CONTRACT_ADDRESS')
    
    if not all([eth_rpc_url, private_key, escrow_contract_address]):
        print("❌ Missing environment variables")
        return
    
    try:
        # Setup Web3
        w3 = Web3(Web3.HTTPProvider(eth_rpc_url))
        account = Account.from_key(private_key)
        
        # Load contract artifact
        escrow_path = "out/UsdcEthXrplEscrow.sol/UsdcEthXrplEscrow.json"
        
        if os.path.exists(escrow_path):
            with open(escrow_path, 'r') as f:
                escrow_artifact = json.load(f)
        else:
            print("❌ Contract artifact not found")
            return
        
        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(escrow_contract_address),
            abi=escrow_artifact['abi']
        )
        
        # Get the last order hash
        try:
            with open('last_order.txt', 'r') as f:
                order_hash_hex = f.read().strip()
                order_hash = bytes.fromhex(order_hash_hex)
                print(f"📋 Order Hash: {order_hash_hex}")
        except FileNotFoundError:
            # Use the order hash from the last run
            order_hash_hex = "f397c4bf64b73dde66cb90d5b697139212e7d7384ff7e3610d9ea674be89647f"
            order_hash = bytes.fromhex(order_hash_hex)
            print(f"📋 Using order hash from last run: {order_hash_hex}")
        
        # Get escrow data
        try:
            escrow_data = contract.functions.getEscrow(order_hash).call()
            print(f"✅ Escrow found")
            print(f"   Maker: {escrow_data[2]}")
            print(f"   Taker: {escrow_data[3]}")
            print(f"   Amount: {escrow_data[6]}")
            print(f"   Hashlock: {escrow_data[1].hex()}")
            
            # Check timelocks
            timelocks = escrow_data[11]  # timelocks tuple
            print(f"   Timelocks:")
            print(f"     src_withdrawal: {timelocks[0]} ({time.ctime(timelocks[0])})")
            print(f"     src_cancellation: {timelocks[1]} ({time.ctime(timelocks[1])})")
            print(f"     dst_withdrawal: {timelocks[2]} ({time.ctime(timelocks[2])})")
            print(f"     dst_cancellation: {timelocks[3]} ({time.ctime(timelocks[3])})")
            
            # Check current time
            current_time = int(time.time())
            print(f"   Current time: {current_time} ({time.ctime(current_time)})")
            
            # Check if we can withdraw
            can_withdraw_after = current_time >= timelocks[0]
            can_withdraw_before = current_time < timelocks[1]
            
            print(f"   Can withdraw (after): {can_withdraw_after}")
            print(f"   Can withdraw (before): {can_withdraw_before}")
            print(f"   Can withdraw (both): {can_withdraw_after and can_withdraw_before}")
            
            # Check if completed
            is_completed = contract.functions.isCompleted(order_hash).call()
            print(f"   Is completed: {is_completed}")
            
            # Check oracle
            oracle_address = contract.functions.xrplOracle().call()
            print(f"   Oracle: {oracle_address}")
            
        except Exception as e:
            print(f"❌ Error getting escrow data: {e}")
            return
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_withdraw() 