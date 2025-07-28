# src/usdc_validator.py
from typing import Dict, Any
import xrpl

# ERC20 ABI for balance checking
ERC20_ABI = [
    {
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class UsdcSwapValidator:
    def __init__(self, eth_manager, xrpl_manager):
        self.eth_manager = eth_manager
        self.xrpl_manager = xrpl_manager
    
    def validate_eth_escrow(self, escrow_address: str, expected_params: dict) -> bool:
        """Validate ETH USDC escrow has correct parameters"""
        try:
            print(f"🔍 Validating ETH escrow at {escrow_address}")
            
            # Check contract exists
            code = self.eth_manager.w3.eth.get_code(escrow_address)
            if code == b'':
                print("❌ Escrow contract not found")
                return False
            
            # Check USDC balance using contract method
            usdc_balance = self.eth_manager.get_usdc_balance(expected_params['usdc_token'])
            
            if usdc_balance < expected_params['amount']:
                print(f"❌ Insufficient USDC in escrow: {usdc_balance} < {expected_params['amount']}")
                return False
            
            print(f"✅ ETH escrow validation passed")
            return True
            
        except Exception as e:
            print(f"❌ ETH escrow validation failed: {e}")
            return False
    
    def validate_xrpl_payment(self, tx_hash: str, expected_params: dict) -> bool:
        """Validate XRPL USDC payment is correct"""
        try:
            print(f"🔍 Validating XRPL payment {tx_hash}")
            return self.xrpl_manager.verify_usdc_payment(tx_hash, expected_params)
        except Exception as e:
            print(f"❌ XRPL payment validation failed: {e}")
            return False
    
    def validate_complete_swap(self, order_hash: str, 
                             eth_escrow_params: dict, 
                             xrpl_payment_params: dict) -> bool:
        """Validate entire swap setup before user reveals secret"""
        
        print(f"🔍 Validating complete swap {order_hash}")
        
        # 1. Validate ETH escrow
        eth_valid = self.validate_eth_escrow(
            eth_escrow_params.get('address', ''), 
            eth_escrow_params
        )
        
        if not eth_valid:
            print("❌ ETH escrow validation failed")
            return False
        
        # 2. Validate XRPL payment
        xrpl_valid = self.validate_xrpl_payment(
            xrpl_payment_params.get('tx_hash', ''),
            xrpl_payment_params
        )
        
        if not xrpl_valid:
            print("❌ XRPL payment validation failed")
            return False
        
        print(f"✅ Swap {order_hash} validation successful")
        return True
    
    def validate_addresses(self, eth_addr: str, xrpl_addr: str) -> bool:
        """Validate ETH and XRPL address formats"""
        try:
            # ETH: 0x... format, 42 characters
            eth_valid = eth_addr.startswith('0x') and len(eth_addr) == 42
            
            # XRPL: r... format, 25-34 characters  
            xrpl_valid = xrpl_addr.startswith('r') and 25 <= len(xrpl_addr) <= 34
            
            if not eth_valid:
                print(f"❌ Invalid ETH address format: {eth_addr}")
            
            if not xrpl_valid:
                print(f"❌ Invalid XRPL address format: {xrpl_addr}")
            
            return eth_valid and xrpl_valid
            
        except Exception as e:
            print(f"❌ Address validation failed: {e}")
            return False
    
    def validate_amounts(self, eth_amount: int, xrpl_amount: str, 
                        min_amount: int = 1000000, max_amount: int = 1000000000) -> bool:
        """Validate swap amounts are reasonable"""
        try:
            # Convert XRPL amount to integer for comparison
            xrpl_amount_int = int(float(xrpl_amount) * 1000000)
            
            # Check minimum amounts
            if eth_amount < min_amount:
                print(f"❌ ETH amount too small: {eth_amount} < {min_amount}")
                return False
            
            if xrpl_amount_int < min_amount:
                print(f"❌ XRPL amount too small: {xrpl_amount_int} < {min_amount}")
                return False
            
            # Check maximum amounts
            if eth_amount > max_amount:
                print(f"❌ ETH amount too large: {eth_amount} > {max_amount}")
                return False
            
            if xrpl_amount_int > max_amount:
                print(f"❌ XRPL amount too large: {xrpl_amount_int} > {max_amount}")
                return False
            
            # Check that amounts are reasonable relative to each other (allow up to 10% difference)
            ratio = abs(eth_amount - xrpl_amount_int) / max(eth_amount, xrpl_amount_int)
            if ratio > 0.1:
                print(f"❌ Amount difference too large: {ratio:.2%}")
                return False
            
            print(f"✅ Amount validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Amount validation failed: {e}")
            return False
    
    def validate_timelocks(self, timelocks: dict, current_time: int = None) -> bool:
        """Validate timelock parameters are reasonable"""
        try:
            import time
            
            if current_time is None:
                current_time = int(time.time())
            
            # Check that all timelocks are in the future
            for name, timestamp in timelocks.items():
                if timestamp <= current_time:
                    print(f"❌ Timelock {name} is in the past: {timestamp} <= {current_time}")
                    return False
            
            # Check timelock ordering
            required_order = [
                'dst_withdrawal',    # User can withdraw first
                'src_withdrawal',    # Then resolver can withdraw
                'dst_cancellation',  # Then destination can be cancelled
                'src_cancellation'   # Finally source can be cancelled
            ]
            
            for i in range(len(required_order) - 1):
                current_lock = required_order[i]
                next_lock = required_order[i + 1]
                
                if current_lock in timelocks and next_lock in timelocks:
                    if timelocks[current_lock] >= timelocks[next_lock]:
                        print(f"❌ Timelock order invalid: {current_lock} >= {next_lock}")
                        return False
            
            print(f"✅ Timelock validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Timelock validation failed: {e}")
            return False