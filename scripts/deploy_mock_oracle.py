#!/usr/bin/env python3
# scripts/deploy_mock_oracle.py
"""
Deploy the mock XRPL Oracle for testing
"""

import os
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

def deploy_mock_oracle():
    """Deploy the mock XRPL Oracle"""
    
    print("🚀 Deploying Mock XRPL Oracle")
    print("=" * 40)
    
    # Load configuration
    eth_rpc_url = os.getenv('ETH_RPC_URL')
    private_key = os.getenv('ETH_PRIVATE_KEY')
    
    if not all([eth_rpc_url, private_key]):
        print("❌ Missing environment variables")
        return
    
    try:
        # Setup Web3
        w3 = Web3(Web3.HTTPProvider(eth_rpc_url))
        account = Account.from_key(private_key)
        
        print(f"🔗 Connected to: {eth_rpc_url}")
        print(f"👤 Account: {account.address}")
        
        # Load contract artifact
        mock_oracle_path = "out/MockXrplOracle.sol/MockXrplOracle.json"
        
        if os.path.exists(mock_oracle_path):
            with open(mock_oracle_path, 'r') as f:
                mock_oracle_artifact = json.load(f)
        else:
            print("❌ Mock oracle artifact not found. Please compile contracts first:")
            print("   forge build")
            return
        
        # Create contract instance
        MockOracle = w3.eth.contract(
            abi=mock_oracle_artifact['abi'],
            bytecode=mock_oracle_artifact['bytecode']['object']
        )
        
        # Build deployment transaction
        construct_txn = MockOracle.constructor().build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address, 'pending'),
            'gas': 2000000,  # High gas limit for deployment
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(construct_txn, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        print(f"📡 Deployment transaction: {tx_hash.hex()}")
        print("⏳ Waiting for confirmation...")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            mock_oracle_address = receipt.contractAddress
            print(f"✅ Mock Oracle deployed successfully!")
            print(f"   Address: {mock_oracle_address}")
            print(f"   Gas used: {receipt.gasUsed}")
            
            # Test the oracle
            print("\n🧪 Testing Mock Oracle...")
            mock_oracle = w3.eth.contract(
                address=mock_oracle_address,
                abi=mock_oracle_artifact['abi']
            )
            
            # Test with dummy values
            test_result = mock_oracle.functions.verifyXrplPayment(
                "FAKE_TX_HASH",
                "0x" + "00" * 32,  # Dummy secret
                "rFAKE_ADDRESS",
                "100.000000"
            ).call()
            
            print(f"   Test result: {test_result}")
            print(f"   Expected: True")
            
            if test_result:
                print("✅ Mock oracle is working correctly!")
                print(f"\n📋 To use this oracle, update your escrow contract:")
                print(f"   python src/update_oracle.py")
                print(f"   Then enter: {mock_oracle_address}")
            else:
                print("❌ Mock oracle test failed!")
                
        else:
            print("❌ Deployment failed!")
            
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy_mock_oracle() 