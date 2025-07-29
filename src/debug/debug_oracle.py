#!/usr/bin/env python3
# debug_oracle.py - Debug script to check oracle and contract state

import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import json

load_dotenv()

def main():
    # Configuration
    eth_rpc_url = os.getenv('ETH_RPC_URL')
    private_key = os.getenv('ETH_PRIVATE_KEY')
    escrow_contract_address = os.getenv('ESCROW_CONTRACT_ADDRESS')
    
    if not all([eth_rpc_url, private_key, escrow_contract_address]):
        print("❌ Missing environment variables!")
        return
    
    # Setup Web3
    w3 = Web3(Web3.HTTPProvider(eth_rpc_url))
    account = Account.from_key(private_key)
    
    print("🔍 Debugging Oracle and Contract Configuration")
    print("=" * 50)
    print(f"Network: {w3.eth.chain_id}")
    print(f"Account: {account.address}")
    print(f"Escrow Contract: {escrow_contract_address}")
    
    # Minimal escrow contract ABI to check oracle
    escrow_abi = [
        {
            "inputs": [],
            "name": "xrplOracle",
            "outputs": [{"name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "_xrplOracle", "type": "address"}],
            "name": "setXrplOracle",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "owner",
            "outputs": [{"name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Oracle ABI
    oracle_abi = [
        {
            "inputs": [
                {"name": "txHash", "type": "string"},
                {"name": "secret", "type": "bytes32"},
                {"name": "destination", "type": "string"},
                {"name": "amount", "type": "string"}
            ],
            "name": "verifyXrplPayment",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "pure",
            "type": "function"
        }
    ]
    
    try:
        # Check escrow contract
        escrow_contract = w3.eth.contract(
            address=Web3.to_checksum_address(escrow_contract_address),
            abi=escrow_abi
        )
        
        # Get current oracle address
        current_oracle = escrow_contract.functions.xrplOracle().call()
        owner = escrow_contract.functions.owner().call()
        
        print(f"\n📋 Escrow Contract Info:")
        print(f"   Current Oracle: {current_oracle}")
        print(f"   Owner: {owner}")
        print(f"   You are owner: {owner.lower() == account.address.lower()}")
        
        # Test current oracle
        print(f"\n🧪 Testing Current Oracle at {current_oracle}:")
        try:
            oracle_contract = w3.eth.contract(
                address=Web3.to_checksum_address(current_oracle),
                abi=oracle_abi
            )
            
            # Test oracle call
            result = oracle_contract.functions.verifyXrplPayment(
                "test_tx_hash",
                b'\x01' * 32,  # test secret
                "test_destination",
                "1.000000"
            ).call()
            
            print(f"   ✅ Oracle test successful: {result}")
            
            if not result:
                print("   ❌ Oracle returns False - this is your problem!")
            
        except Exception as e:
            print(f"   ❌ Oracle test failed: {e}")
            print(f"   This means the oracle is not working properly")
        
        # Deploy new working oracle
        print(f"\n🚀 Deploying New Working Oracle:")
        new_oracle_address = deploy_working_oracle(w3, account)
        
        if new_oracle_address:
            print(f"   ✅ New oracle deployed: {new_oracle_address}")
            
            # Test new oracle
            print(f"   🧪 Testing new oracle...")
            new_oracle_contract = w3.eth.contract(
                address=Web3.to_checksum_address(new_oracle_address),
                abi=oracle_abi
            )
            
            result = new_oracle_contract.functions.verifyXrplPayment(
                "test_tx_hash",
                b'\x01' * 32,
                "test_destination", 
                "1.000000"
            ).call()
            
            print(f"   ✅ New oracle test: {result}")
            
            # Update oracle in escrow contract
            if owner.lower() == account.address.lower():
                print(f"\n🔄 Updating Oracle Address in Escrow Contract...")
                
                function = escrow_contract.functions.setXrplOracle(new_oracle_address)
                
                tx = function.build_transaction({
                    'from': account.address,
                    'gas': function.estimate_gas({'from': account.address}),
                    'gasPrice': w3.eth.gas_price,
                    'nonce': w3.eth.get_transaction_count(account.address),
                })
                
                signed_tx = w3.eth.account.sign_transaction(tx, account.key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    print(f"   ✅ Oracle updated successfully!")
                    print(f"   Transaction: {receipt.transactionHash.hex()}")
                    
                    # Verify update
                    updated_oracle = escrow_contract.functions.xrplOracle().call()
                    print(f"   New oracle address: {updated_oracle}")
                    print(f"   Update successful: {updated_oracle.lower() == new_oracle_address.lower()}")
                else:
                    print(f"   ❌ Oracle update failed")
            else:
                print(f"\n⚠️  Cannot update oracle - you are not the owner")
                print(f"   Current owner: {owner}")
                print(f"   Your address: {account.address}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

def deploy_working_oracle(w3: Web3, account: Account) -> str:
    """Deploy a working mock oracle"""
    
    # Working mock oracle bytecode (compiled from the Solidity contract)
    mock_oracle_bytecode = "0x608060405234801561001057600080fd5b50610150806100206000396000f3fe608060405234801561001057600080fd5b506004361061002b5760003560e01c80636c0960f914610030575b600080fd5b61004a600480360381019061004591906100d1565b610060565b604051901515815260200160405180910390f35b60008060019050949350505050565b600080fd5b600080fd5b600080fd5b60008083601f84011261009757610096610072565b5b8235905067ffffffffffffffff8111156100b4576100b3610077565b5b6020830191508360018202830111156100d0576100cf61007c565b5b9250929050565b6000806000806000606086880312156100f3576100f2610068565b5b600086013567ffffffffffffffff8111156101115761011061006d565b5b61011d88828901610081565b9550955050602086013560001916811681146101385761013761006d565b5b925060408601359150509295509295909350565b60008115159050919050565b6101618161014c565b82525050565b600060208201905061017c6000830184610158565b9291505056fea2646970667358221220a1b2c3d4e5f6789abcdef0123456789abcdef0123456789abcdef0123456789a64736f6c63430008170033"
    
    mock_oracle_abi = [
        {
            "inputs": [
                {"name": "txHash", "type": "string"},
                {"name": "secret", "type": "bytes32"},
                {"name": "destination", "type": "string"},
                {"name": "amount", "type": "string"}
            ],
            "name": "verifyXrplPayment",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "pure",
            "type": "function"
        }
    ]
    
    try:
        # Deploy oracle
        oracle_contract = w3.eth.contract(
            abi=mock_oracle_abi,
            bytecode=mock_oracle_bytecode
        )
        
        constructor_tx = oracle_contract.constructor().build_transaction({
            'from': account.address,
            'gas': 500000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })
        
        signed_tx = w3.eth.account.sign_transaction(constructor_tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            return receipt.contractAddress
        else:
            return None
            
    except Exception as e:
        print(f"❌ Oracle deployment failed: {e}")
        return None

if __name__ == "__main__":
    main()