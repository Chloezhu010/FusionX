#!/usr/bin/env python3
# src/update_oracle.py
"""
Script to update the escrow contract to use a new oracle address
"""

import os
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

def load_contract_artifacts():
    """Load compiled contract artifacts"""
    try:
        escrow_path = "out/UsdcEthXrplEscrow.sol/UsdcEthXrplEscrow.json"
        
        if os.path.exists(escrow_path):
            with open(escrow_path, 'r') as f:
                escrow_artifact = json.load(f)
            return escrow_artifact
        else:
            print("❌ Contract artifacts not found. Please compile contracts first:")
            print("   forge build")
            return None
            
    except Exception as e:
        print(f"❌ Error loading contract artifacts: {e}")
        return None

def update_oracle():
    """Update the escrow contract to use a new oracle address"""
    
    print("🔧 Updating Escrow Contract Oracle")
    print("=" * 50)
    
    # Load configuration
    eth_rpc_url = os.getenv('ETH_RPC_URL')
    private_key = os.getenv('ETH_PRIVATE_KEY')
    escrow_contract_address = os.getenv('ESCROW_CONTRACT_ADDRESS')
    
    if not all([eth_rpc_url, private_key, escrow_contract_address]):
        print("❌ Missing required environment variables:")
        print("   ETH_RPC_URL: Ethereum RPC endpoint")
        print("   ETH_PRIVATE_KEY: Private key for deployment")
        print("   ESCROW_CONTRACT_ADDRESS: Current escrow contract address")
        return
    
    try:
        # Setup Web3 connection
        print(f"🔗 Connecting to {eth_rpc_url}")
        w3 = Web3(Web3.HTTPProvider(eth_rpc_url))
        
        if not w3.is_connected():
            print("❌ Failed to connect to Ethereum network")
            return
        
        # Load account
        account = Account.from_key(private_key)
        print(f"👤 Account: {account.address}")
        
        # Load contract artifact
        artifact = load_contract_artifacts()
        if not artifact:
            return
        
        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(escrow_contract_address),
            abi=artifact['abi']
        )
        
        # Get current oracle
        try:
            current_oracle = contract.functions.xrplOracle().call()
            print(f"📋 Current Oracle: {current_oracle}")
        except Exception as e:
            print(f"⚠️  Could not get current oracle: {e}")
            current_oracle = "Unknown"
        
        # Get owner
        try:
            owner = contract.functions.owner().call()
            print(f"👑 Contract Owner: {owner}")
            print(f"   You are owner: {account.address.lower() == owner.lower()}")
        except Exception as e:
            print(f"⚠️  Could not get owner: {e}")
            owner = "Unknown"
        
        # Check if you're the owner
        if account.address.lower() != owner.lower():
            print("❌ You are not the contract owner. Only the owner can update the oracle.")
            return
        
        # Get new oracle address
        # Use the mock oracle address for testing
    new_oracle_address = "0xCCC55931f5036EDDC46507342749aBF7e56d28dd"
    print(f"\n🔧 Using mock oracle address: {new_oracle_address}")
        
        if not new_oracle_address.startswith('0x') or len(new_oracle_address) != 42:
            print("❌ Invalid oracle address format")
            return
        
        # Confirm update
        print(f"\n🤔 Update oracle from {current_oracle} to {new_oracle_address}?")
        confirm = input("Proceed? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Oracle update cancelled")
            return
        
        # Build transaction
        function = contract.functions.setXrplOracle(new_oracle_address)
        
        # Estimate gas
        gas_estimate = function.estimate_gas({'from': account.address})
        print(f"⛽ Estimated gas: {gas_estimate:,}")
        
        # Build transaction
        tx = function.build_transaction({
            'from': account.address,
            'gas': int(gas_estimate * 1.2),  # Add 20% buffer
            'gasPrice': int(w3.eth.gas_price * 1.1),
            'nonce': w3.eth.get_transaction_count(account.address, 'pending')
        })
        
        # Sign and send
        signed_tx = w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"📡 Oracle update transaction: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print("✅ Oracle updated successfully!")
            print(f"   Gas used: {receipt.gasUsed:,}")
            
            # Verify the update
            try:
                updated_oracle = contract.functions.xrplOracle().call()
                print(f"✅ New Oracle: {updated_oracle}")
                print(f"   Matches input: {updated_oracle.lower() == new_oracle_address.lower()}")
            except Exception as e:
                print(f"⚠️  Could not verify oracle update: {e}")
        else:
            print("❌ Oracle update failed")
            
    except Exception as e:
        print(f"❌ Oracle update failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_oracle() 