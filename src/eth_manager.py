# src/eth_manager.py
from web3 import Web3
from eth_account import Account
import json
import time
import os
from typing import Dict

class EthEscrowManager:
    def __init__(self, provider_url: str, private_key: str, contract_address: str):
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.account = Account.from_key(private_key)
        self.contract_address = contract_address
        
        # ABI for the UsdcEthXrplEscrow contract (simplified for demo)
        self.contract_abi = [
            {
                "inputs": [
                    {
                        "components": [
                            {"name": "orderHash", "type": "bytes32"},
                            {"name": "hashlock", "type": "bytes32"},
                            {"name": "maker", "type": "address"},
                            {"name": "taker", "type": "address"},
                            {"name": "xrplDestination", "type": "string"},
                            {"name": "usdcToken", "type": "address"},
                            {"name": "amount", "type": "uint256"},
                            {"name": "safetyDeposit", "type": "uint256"},
                            {"name": "xrplCurrency", "type": "string"},
                            {"name": "xrplIssuer", "type": "string"},
                            {"name": "xrplAmount", "type": "string"},
                            {
                                "components": [
                                    {"name": "srcWithdrawal", "type": "uint256"},
                                    {"name": "srcCancellation", "type": "uint256"},
                                    {"name": "dstWithdrawal", "type": "uint256"},
                                    {"name": "dstCancellation", "type": "uint256"}
                                ],
                                "name": "timelocks",
                                "type": "tuple"
                            }
                        ],
                        "name": "params",
                        "type": "tuple"
                    }
                ],
                "name": "createEscrow",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "secret", "type": "bytes32"},
                    {"name": "orderHash", "type": "bytes32"},
                    {"name": "xrplTxHash", "type": "string"}
                ],
                "name": "withdraw",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "orderHash", "type": "bytes32"}],
                "name": "cancel",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "orderHash", "type": "bytes32"}],
                "name": "getEscrow",
                "outputs": [
                    {
                        "components": [
                            {"name": "orderHash", "type": "bytes32"},
                            {"name": "hashlock", "type": "bytes32"},
                            {"name": "maker", "type": "address"},
                            {"name": "taker", "type": "address"},
                            {"name": "xrplDestination", "type": "string"},
                            {"name": "usdcToken", "type": "address"},
                            {"name": "amount", "type": "uint256"},
                            {"name": "safetyDeposit", "type": "uint256"},
                            {"name": "xrplCurrency", "type": "string"},
                            {"name": "xrplIssuer", "type": "string"},
                            {"name": "xrplAmount", "type": "string"},
                            {
                                "components": [
                                    {"name": "srcWithdrawal", "type": "uint256"},
                                    {"name": "srcCancellation", "type": "uint256"},
                                    {"name": "dstWithdrawal", "type": "uint256"},
                                    {"name": "dstCancellation", "type": "uint256"}
                                ],
                                "name": "timelocks",
                                "type": "tuple"
                            }
                        ],
                        "name": "",
                        "type": "tuple"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "orderHash", "type": "bytes32"}],
                "name": "isCompleted",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=self.contract_abi
        )
    
    def create_escrow(self, params: Dict) -> str:
        """Create new escrow"""
        print(f"📝 Creating escrow for {params['amount'] / 10**6} USDC...")
        print(f"   Raw amount: {params['amount']} units")
        print(f"   USDC Token: {params['usdc_token']}")
        print(f"   Spender (contract): {self.contract.address}")
        
        # Build escrow parameters tuple, ensuring all addresses are checksummed
        escrow_params = (
            params['order_hash'],
            params['hashlock'], 
            self.w3.to_checksum_address(params['maker']),
            self.w3.to_checksum_address(params['taker']),
            params['xrpl_destination'],
            self.w3.to_checksum_address(params['usdc_token']),
            params['amount'],
            params['safety_deposit'],
            params['xrpl_currency'],
            params['xrpl_issuer'],
            params['xrpl_amount'],
            (
                params['timelocks']['src_withdrawal'],
                params['timelocks']['src_cancellation'],
                params['timelocks']['dst_withdrawal'],
                params['timelocks']['dst_cancellation']
            )
        )
        
        # Build transaction
        function = self.contract.functions.createEscrow(escrow_params)
        
        # Estimate gas
        gas_estimate = function.estimate_gas({
            'from': self.account.address,
            'value': params['safety_deposit']
        })
        
        # Build transaction
        tx = function.build_transaction({
            'from': self.account.address,
            'gas': int(gas_estimate * 1.2),  # Add 20% buffer
            'gasPrice': int(self.w3.eth.gas_price * 2.0),  # Double gas price for faster mining
            'nonce': self.w3.eth.get_transaction_count(self.account.address, 'pending'),
            'value': params['safety_deposit']
        })
        
        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"✅ Escrow created - Gas used: {receipt.gasUsed}")
        return receipt.transactionHash.hex()
    
    def approve_usdc(self, usdc_address: str, spender: str, amount: int) -> str:
        """Approve the spender to withdraw USDC on behalf of the user"""
        print(f"👍 Approving {amount / 10**6} USDC for spender {spender}...")
        print(f"   Raw amount: {amount} units")
        
        # Minimal ABI for ERC20 approve function
        approve_abi = [
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

        usdc_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(usdc_address),
            abi=approve_abi
        )

        # Build transaction with robust gas settings
        function = usdc_contract.functions.approve(self.w3.to_checksum_address(spender), amount)
        
        # Check account balance first
        eth_balance = self.w3.eth.get_balance(self.account.address)
        print(f"   Account ETH balance: {eth_balance / 10**18:.6f} ETH")
        
        try:
            gas_estimate = function.estimate_gas({'from': self.account.address})
            print(f"   Estimated gas: {gas_estimate}")
        except Exception as e:
            print(f"❌ Gas estimation failed: {e}")
            raise Exception(f"Gas estimation failed: {e}")
        
        current_gas_price = self.w3.eth.gas_price
        adjusted_gas_price = int(current_gas_price * 1.5)  # 50% higher for reliability
        
        estimated_cost = gas_estimate * adjusted_gas_price
        print(f"   Estimated transaction cost: {estimated_cost / 10**18:.6f} ETH")
        
        if eth_balance < estimated_cost:
            raise Exception(f"Insufficient ETH for gas. Need {estimated_cost / 10**18:.6f} ETH, have {eth_balance / 10**18:.6f} ETH")
        
        tx = function.build_transaction({
            'from': self.account.address,
            'gas': gas_estimate,
            'gasPrice': adjusted_gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address, 'pending')
        })

        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"📡 Approval transaction hash: {tx_hash.hex()}")
        print(f"   Gas limit: {tx['gas']}")
        print(f"   Gas price: {tx['gasPrice']} wei ({tx['gasPrice'] / 10**9:.2f} gwei)")
        print(f"   From: {tx['from']}")
        print(f"   To: {usdc_address}")
        
        # CRITICAL: Wait for approval to be confirmed before returning
        print(f"⏳ Waiting for approval transaction to be confirmed...")
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)  # 5 minute timeout
            
            if receipt.status == 1:
                print(f"✅ Approval confirmed - Gas used: {receipt.gasUsed}")
            else:
                print(f"❌ Approval transaction failed!")
                print(f"   Transaction receipt: {receipt}")
                raise Exception("Approval transaction failed")
        except Exception as e:
            print(f"❌ Error waiting for approval confirmation: {e}")
            print(f"   You can check the transaction status at: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
            raise Exception("Approval transaction failed")
        
        # Verify the allowance was set correctly
        print(f"🔍 Verifying allowance...")
        allowance = self.check_usdc_allowance(usdc_address, spender)
        print(f"   Current allowance: {allowance / 10**6} USDC ({allowance} units)")
        
        if allowance >= amount:
            print(f"✅ Allowance verified successfully")
        else:
            print(f"❌ Allowance verification failed! Expected: {amount}, Got: {allowance}")
            
        return receipt.transactionHash.hex()
    
    def check_usdc_allowance(self, usdc_address: str, spender: str) -> int:
        """Check the current USDC allowance for a spender"""
        allowance_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        usdc_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(usdc_address),
            abi=allowance_abi
        )
        
        allowance = usdc_contract.functions.allowance(
            self.account.address,
            self.w3.to_checksum_address(spender)
        ).call()
        
        return allowance
    
    def withdraw_escrow(self, secret: bytes, order_hash: bytes, xrpl_tx_hash: str) -> str:
        """Withdraw from escrow with secret and XRPL proof"""
        
        print("\n--- Preparing to Withdraw Escrow ---")
        print(f"  - Order Hash: {order_hash.hex()}")
        print(f"  - Secret: {secret.hex()}")
        print(f"  - XRPL TX Hash: {xrpl_tx_hash}")
        print(f"  - Withdrawing Account (Taker): {self.account.address}")

        # Let's fetch the escrow from the chain to double-check its state
        try:
            stored_escrow = self.contract.functions.getEscrow(order_hash).call()
            onchain_taker = stored_escrow[3]
            onchain_hashlock = stored_escrow[1]
            is_complete = self.contract.functions.isCompleted(order_hash).call()
            
            print("\n  - Verifying On-Chain Escrow State:")
            print(f"    - On-Chain Taker: {onchain_taker}")
            print(f"    - On-Chain Hashlock: {onchain_hashlock.hex()}")
            print(f"    - Is Already Completed? {is_complete}")
            
            # Perform local checks to predict the failure
            print("\n  - Pre-flight Checks:")
            print(f"    - CHECK 1 (Taker Match): {self.account.address == onchain_taker}")
            print(f"    - CHECK 2 (Secret Match): {Web3.keccak(secret) == onchain_hashlock}")

        except Exception as e:
            print(f"  - CRITICAL: Could not fetch escrow state from chain: {e}")

        function = self.contract.functions.withdraw(
            secret,
            order_hash,
            xrpl_tx_hash
        )
        
        print("\n  - Estimating gas for withdrawal...")
        
        # Build transaction with robust gas settings
        tx = function.build_transaction({
            'from': self.account.address,
            'gas': function.estimate_gas({'from': self.account.address}),
            'gasPrice': int(self.w3.eth.gas_price * 1.2),
            'nonce': self.w3.eth.get_transaction_count(self.account.address, 'pending')
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Escrow withdrawn - Gas used: {receipt.gasUsed}")
        return receipt.transactionHash.hex()
    
    def cancel_escrow(self, order_hash: bytes) -> str:
        """Cancel escrow after timeout"""
        function = self.contract.functions.cancel(order_hash)
        
        # Build transaction with robust gas settings
        tx = function.build_transaction({
            'from': self.account.address,
            'gas': function.estimate_gas({'from': self.account.address}),
            'gasPrice': int(self.w3.eth.gas_price * 1.2),
            'nonce': self.w3.eth.get_transaction_count(self.account.address, 'pending')
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Escrow cancelled - Gas used: {receipt.gasUsed}")
        return receipt.transactionHash.hex()
    
    def get_escrow_status(self, order_hash: bytes) -> dict:
        """Get escrow status"""
        try:
            escrow_data = self.contract.functions.getEscrow(order_hash).call()
            is_completed = self.contract.functions.isCompleted(order_hash).call()
            
            return {
                'exists': escrow_data[0] != b'\x00' * 32,  # Check if orderHash is not zero
                'completed': is_completed,
                'maker': escrow_data[2],
                'taker': escrow_data[3],
                'amount': escrow_data[6],
                'xrpl_destination': escrow_data[4],
                'xrpl_amount': escrow_data[10]
            }
        except Exception as e:
            return {'exists': False, 'error': str(e)}

    def get_account_balance(self) -> float:
        """Get ETH balance of the account"""
        balance_wei = self.w3.eth.get_balance(self.account.address)
        return self.w3.from_wei(balance_wei, 'ether')
    
    def get_usdc_balance(self, usdc_address: str) -> int:
        """Get USDC balance of the account"""
        try:
            usdc_abi = [
                {
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            usdc_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(usdc_address),
                abi=usdc_abi
            )
            
            return usdc_contract.functions.balanceOf(self.account.address).call()
        except Exception as e:
            print(f"⚠️  Could not check USDC balance (contract may not exist on testnet): {e}")
            print(f"   This is normal for testnets - continuing with 0 balance")
            return 0  # Return 0 instead of crashing 