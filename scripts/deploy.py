#!/usr/bin/env python3
# scripts/deploy.py
"""
Deployment script for FusionX USDC escrow contracts
"""

import os
import json
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

def load_contract_artifacts():
    """Load compiled contract artifacts"""
    try:
        # Try to load from Foundry output
        base_escrow_path = "out/BaseEscrow.sol/BaseEscrow.json"
        escrow_path = "out/UsdcEthXrplEscrow.sol/UsdcEthXrplEscrow.json"
        
        if os.path.exists(base_escrow_path) and os.path.exists(escrow_path):
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

def deploy_mock_oracle(w3: Web3, account: Account) -> str:
    """Deploy a mock XRPL oracle for testing"""
    
    # Simple mock oracle that always returns true
    mock_oracle_bytecode = "0x608060405234801561001057600080fd5b50610150806100206000396000f3fe608060405234801561001057600080fd5b506004361061002b5760003560e01c80636c0960f914610030575b600080fd5b61004a600480360381019061004591906100d1565b610060565b604051610057919061010d565b60405180910390f35b60008060019050949350505050565b600080fd5b600080fd5b600080fd5b600080fd5b600080fd5b60008083601f84011261009757610096610072565b5b8235905067ffffffffffffffff8111156100b4576100b3610077565b5b6020830191508360018202830111156100d0576100cf61007c565b5b9250929050565b6000806000806000606086880312156100f3576100f2610068565b5b600086013567ffffffffffffffff8111156101115761011061006d565b5b61011d88828901610081565b9550955050602086013560001916811681146101385761013761006d565b5b925060408601359150509295509295909350565b60008115159050919050565b6101618161014c565b82525050565b600060208201905061017c6000830184610158565b9291505056fea2646970667358221220a1b2c3d4e5f6789abcdef0123456789abcdef0123456789abcdef0123456789a64736f6c63430008170033"
    
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
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Deploy mock oracle
    oracle_contract = w3.eth.contract(
        abi=mock_oracle_abi,
        bytecode=mock_oracle_bytecode
    )
    
    # Build deployment transaction
    constructor_tx = oracle_contract.constructor().build_transaction({
        'from': account.address,
        'gas': 500000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
    })
    
    # Sign and send
    signed_tx = w3.eth.account.sign_transaction(constructor_tx, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"📡 Mock oracle deployment tx: {tx_hash.hex()}")
    
    # Wait for deployment
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status == 1:
        print(f"✅ Mock Oracle deployed at: {receipt.contractAddress}")
        print(f"   Gas used: {receipt.gasUsed:,}")
        return receipt.contractAddress
    else:
        raise Exception("Mock oracle deployment failed")

def deploy_escrow_contract(w3: Web3, account: Account, oracle_address: str) -> str:
    """Deploy the main USDC escrow contract"""
    
    # Load contract artifact
    artifact = load_contract_artifacts()
    if not artifact:
        return None
    
    # Create contract instance
    contract = w3.eth.contract(
        abi=artifact['abi'],
        bytecode=artifact['bytecode']['object']
    )
    
    # Build deployment transaction
    constructor_tx = contract.constructor(oracle_address).build_transaction({
        'from': account.address,
        'gas': 3000000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
    })
    
    # Sign and send
    signed_tx = w3.eth.account.sign_transaction(constructor_tx, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"📡 Escrow contract deployment tx: {tx_hash.hex()}")
    
    # Wait for deployment
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status == 1:
        print(f"✅ USDC Escrow Contract deployed at: {receipt.contractAddress}")
        print(f"   Gas used: {receipt.gasUsed:,}")
        return receipt.contractAddress
    else:
        raise Exception("Escrow contract deployment failed")

def verify_deployment(w3: Web3, contract_address: str):
    """Verify the deployed contract"""
    
    # Load contract artifact  
    artifact = load_contract_artifacts()
    if not artifact:
        return False
    
    try:
        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=artifact['abi']
        )
        
        # Test contract is callable (check if it has the owner function)
        try:
            owner = contract.functions.owner().call()
            print(f"✅ Contract verification successful")
            print(f"   Owner: {owner}")
            return True
        except Exception as e:
            print(f"⚠️  Contract deployed but verification failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Contract verification failed: {e}")
        return False

def save_deployment_info(contract_address: str, oracle_address: str, network: str, tx_hash: str):
    """Save deployment information to a file"""
    
    deployment_info = {
        'network': network,
        'timestamp': int(time.time()),
        'escrow_contract': contract_address,
        'oracle_contract': oracle_address,
        'deployment_tx': tx_hash,
        'deployer': os.getenv('ETH_PRIVATE_KEY') and Account.from_key(os.getenv('ETH_PRIVATE_KEY')).address
    }
    
    # Save to file
    with open('deployment.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    print(f"💾 Deployment info saved to deployment.json")

def main():
    """Main deployment function"""
    
    print("🚀 FusionX Contract Deployment")
    print("=" * 50)
    
    # Load configuration
    eth_rpc_url = os.getenv('ETH_RPC_URL')
    private_key = os.getenv('ETH_PRIVATE_KEY')
    
    if not eth_rpc_url or not private_key:
        print("❌ Missing required environment variables:")
        print("   ETH_RPC_URL: Ethereum RPC endpoint")
        print("   ETH_PRIVATE_KEY: Private key for deployment")
        print("\nPlease set these in your .env file")
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
        print(f"👤 Deployer: {account.address}")
        
        # Check balance
        balance = w3.eth.get_balance(account.address)
        balance_eth = w3.from_wei(balance, 'ether')
        print(f"💰 Balance: {balance_eth:.4f} ETH")
        
        if balance_eth < 0.1:
            print("⚠️  Low balance! Make sure you have enough ETH for deployment")
        
        # Get network info
        chain_id = w3.eth.chain_id
        network_names = {
            1: "Mainnet",
            5: "Goerli", 
            11155111: "Sepolia",
            137: "Polygon",
            80001: "Polygon Mumbai"
        }
        network_name = network_names.get(chain_id, f"Chain {chain_id}")
        print(f"🌐 Network: {network_name} (Chain ID: {chain_id})")
        
        # Confirm deployment
        confirm = input(f"\n🤔 Deploy to {network_name}? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Deployment cancelled")
            return
        
        print("\n📋 Starting deployment...")
        
        # Step 1: Deploy mock oracle
        print("\n1️⃣  Deploying Mock XRPL Oracle...")
        oracle_address = deploy_mock_oracle(w3, account)
        
        # Step 2: Deploy main escrow contract
        print("\n2️⃣  Deploying USDC Escrow Contract...")
        escrow_address = deploy_escrow_contract(w3, account, oracle_address)
        
        if not escrow_address:
            print("❌ Escrow contract deployment failed")
            return
        
        # Step 3: Verify deployment
        print("\n3️⃣  Verifying deployment...")
        if verify_deployment(w3, escrow_address):
            print("✅ Deployment verification successful")
        
        # Step 4: Save deployment info
        print("\n4️⃣  Saving deployment information...")
        save_deployment_info(escrow_address, oracle_address, network_name, "")
        
        # Final summary
        print("\n" + "=" * 50)
        print("🎉 Deployment Complete!")
        print(f"   Escrow Contract: {escrow_address}")
        print(f"   Oracle Contract: {oracle_address}")
        print(f"   Network: {network_name}")
        print("\n📝 Next steps:")
        print("   1. Update your .env file with:")
        print(f"      ESCROW_CONTRACT_ADDRESS={escrow_address}")
        print("   2. Run tests: python -m pytest tests/")
        print("   3. Execute swaps: python src/main.py")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 