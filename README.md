# FusionX - Cross-Chain USDC Swaps

**FusionX** enables atomic swaps of USDC between Ethereum and XRPL using smart contracts and cryptographic secrets to ensure security and atomicity.

## 🚀 Features

- ✅ **Atomic Swaps** - Either both sides complete or both fail
- ✅ **USDC Support** - Swap USDC between Ethereum and XRPL
- ✅ **Security** - Uses hash-time-locked contracts (HTLCs) and safety deposits
- ✅ **Partial Fills** - Support for partial order execution
- ✅ **Cancellation** - Built-in timeout and cancellation mechanisms
- ✅ **Testing** - Comprehensive test suite with mocked components

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│   Ethereum (ETH)    │    │      XRPL           │
│                     │    │                     │
│  ┌───────────────┐  │    │  ┌───────────────┐  │
│  │ USDC Escrow   │  │◄──►│  │ USDC Payment  │  │
│  │ Contract      │  │    │  │ Transaction   │  │
│  └───────────────┘  │    │  └───────────────┘  │
│                     │    │                     │
│ User deposits USDC  │    │ Resolver sends     │
│ + Safety deposit    │    │ USDC to user      │
└─────────────────────┘    └─────────────────────┘
           ▲                           ▲
           │                           │
           └──────── Resolver ─────────┘
           (Facilitates the swap)
```

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js** (for XRPL connections)
- **Foundry** (for smart contract compilation)
- **Git**

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd FusionX
```

### 2. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Foundry (for smart contracts)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### 3. Install OpenZeppelin Contracts
```bash
# Install OpenZeppelin contracts for Solidity
forge install OpenZeppelin/openzeppelin-contracts
```

### 4. Compile Smart Contracts
```bash
forge build
```

### 5. Set Up Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your actual values
nano .env
```

Example `.env` configuration:
```env
# Ethereum Configuration (Use Sepolia testnet for testing)
ETH_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID
ETH_PRIVATE_KEY=0xYOUR_ETHEREUM_PRIVATE_KEY_HERE
ESCROW_CONTRACT_ADDRESS=0xYOUR_DEPLOYED_CONTRACT_ADDRESS

# XRPL Configuration (Use testnet for testing)
XRPL_RPC_URL=wss://s.altnet.rippletest.net:51233
XRPL_WALLET_SEED=sYOUR_XRPL_WALLET_SEED_HERE

# Token Addresses
ETH_USDC_ADDRESS=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
XRPL_USDC_ISSUER=rcEGREd5YGXK2grCkeSNRZm2Diq1Hp5jk
```

## 🚀 Quick Start

### 1. Deploy Smart Contracts
```bash
python scripts/deploy.py
```

This will:
- Deploy a mock XRPL oracle
- Deploy the USDC escrow contract
- Save deployment info to `deployment.json`
- Update your `.env` with the contract address

### 2. Run Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_usdc_swap.py -v
```

### 3. Check Balances
```bash
python src/main.py
# Choose option 3: Check balances
```

### 4. Execute a Test Swap
```bash
python src/main.py
# Choose option 1: Execute example ETH → XRPL swap
```

## 📖 Usage Guide

### Basic Swap Flow

1. **Create Order**: User creates a cross-chain swap order
2. **Deploy Escrow**: Resolver deploys escrow on Ethereum with user's USDC
3. **Send XRPL Payment**: Resolver sends USDC to user on XRPL
4. **User Validation**: User validates XRPL payment off-chain
5. **Secret Sharing**: User shares secret to complete swap
6. **Withdrawal**: Resolver withdraws USDC from Ethereum escrow

### Command Line Interface

```bash
python src/main.py
```

Available options:
- **1**: Execute example ETH → XRPL swap
- **2**: Check swap status
- **3**: Check account balances
- **4**: Interactive swap creation
- **5**: Show current configuration
- **0**: Exit

### Interactive Swap Creation

```bash
python src/main.py
# Choose option 4: Interactive swap creation

# You'll be prompted for:
# - ETH user address (0x...)
# - XRPL user address (r...)
# - USDC amount to swap
# - Fee rate (e.g., 0.01 for 1%)
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test class
python -m pytest tests/test_usdc_swap.py::TestUsdcSwap -v
```

### Integration Tests
```bash
# Run integration tests (requires deployed contracts)
python -m pytest tests/test_usdc_swap.py::TestIntegration -v
```

### Manual Testing

1. **Balance Checking**:
```bash
python src/main.py  # Option 3
```

2. **Contract Deployment**:
```bash
python scripts/deploy.py
```

3. **Swap Execution**:
```bash
python src/main.py  # Option 1 or 4
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ETH_RPC_URL` | Ethereum RPC endpoint | `https://sepolia.infura.io/v3/...` |
| `ETH_PRIVATE_KEY` | Ethereum private key | `0x1234...` |
| `ESCROW_CONTRACT_ADDRESS` | Deployed escrow contract | `0xabcd...` |
| `XRPL_RPC_URL` | XRPL RPC endpoint | `wss://s.altnet.rippletest.net:51233` |
| `XRPL_WALLET_SEED` | XRPL wallet seed | `sXXXXXXXXXXXXXXXX` |
| `ETH_USDC_ADDRESS` | USDC contract on the network | `0x94a9D9...` (Sepolia) |
| `XRPL_USDC_ISSUER` | USDC issuer on XRPL | (Find a valid testnet issuer) |

### Network Configuration

#### Testnets (Recommended for Development)
```env
# Ethereum Sepolia
ETH_RPC_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
ETH_USDC_ADDRESS=0x1xxx...

# XRPL Testnet
XRPL_RPC_URL=wss://s.altnet.rippletest.net:51233
```

#### Mainnets (Production)
```env
# Ethereum Mainnet
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
ETH_USDC_ADDRESS=0xA0...

# XRPL Mainnet
XRPL_RPC_URL=wss://xrplcluster.com
```

## 📝 API Reference

### UsdcCrossChainResolver

Main class for executing cross-chain swaps.

```python
from src.usdc_resolver import UsdcCrossChainResolver

resolver = UsdcCrossChainResolver(eth_manager, xrpl_manager)

# Execute a swap
result = await resolver.execute_usdc_swap(order)

# Check swap status
status = resolver.get_swap_status(order_hash)

# Cancel a swap
result = await resolver.cancel_swap(order_hash)
```

### EthEscrowManager

Manages Ethereum escrow contracts.

```python
from src.eth_manager import EthEscrowManager

eth_manager = EthEscrowManager(rpc_url, private_key, contract_address)

# Create escrow
tx_hash = eth_manager.create_escrow(params)

# Withdraw from escrow
tx_hash = eth_manager.withdraw_escrow(secret, order_hash, xrpl_tx_hash)

# Get escrow status
status = eth_manager.get_escrow_status(order_hash)
```

### XrplUsdcManager

Manages XRPL USDC payments.

```python
from src.xrpl_usdc_manager import XrplUsdcManager
import xrpl

wallet = xrpl.Wallet.from_seed(seed)
xrpl_manager = XrplUsdcManager(rpc_url, wallet)

# Send USDC payment
tx_hash = xrpl_manager.send_usdc_payment(destination, amount)

# Check USDC balance
balance = xrpl_manager.check_usdc_balance(account)
```

## 🔒 Security Considerations

### Smart Contract Security
- ✅ **Reentrancy Protection** - Uses OpenZeppelin's ReentrancyGuard
- ✅ **Access Control** - Only authorized parties can call functions
- ✅ **Time Locks** - Built-in timeouts for all operations
- ✅ **Safety Deposits** - Economic incentives prevent malicious behavior

### Operational Security
- 🔑 **Private Key Management** - Store private keys securely
- 🌐 **Network Selection** - Use testnets for development
- 💰 **Amount Limits** - Start with small amounts for testing
- ⏰ **Timelock Validation** - Verify timeout parameters

### User Validation Process
Users must validate the following before sharing their secret:
1. **XRPL Payment Exists** - Check transaction hash on XRPL
2. **Correct Amount** - Verify USDC amount matches expectation
3. **Correct Destination** - Confirm payment goes to user's address
4. **Correct Token** - Ensure it's USDC from correct issuer

## 🐛 Troubleshooting

### Common Issues

#### 1. Contract Compilation Errors
```bash
# Install OpenZeppelin contracts
forge install OpenZeppelin/openzeppelin-contracts

# Clean and rebuild
forge clean
forge build
```

#### 2. RPC Connection Issues
```bash
# Test connection
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  YOUR_ETH_RPC_URL
```

#### 3. XRPL Connection Issues
- Ensure XRPL RPC URL is correct
- Check wallet seed format
- Verify network (testnet vs mainnet)

#### 4. Transaction Failures
- Check gas limits and prices
- Verify account has sufficient balance
- Confirm contract addresses are correct

### Debug Mode
```bash
# Enable debug logging
export DEBUG=1
python src/main.py
```

### Getting Help

1. **Check Logs** - Review console output for error details
2. **Run Tests** - Verify your setup with `python -m pytest tests/ -v`
3. **Check Configuration** - Use option 5 in main menu
4. **Review Deployment** - Check `deployment.json` for contract addresses

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run linting
black src/ tests/
flake8 src/ tests/

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Project Structure
```
Xinch/
├── contracts/           # Solidity smart contracts
│   ├── BaseEscrow.sol
│   └── UsdcEthXrplEscrow.sol
├── src/                # Python source code
│   ├── main.py         # Main CLI interface
│   ├── eth_manager.py  # Ethereum interactions
│   ├── xrpl_usdc_manager.py  # XRPL interactions
│   ├── usdc_resolver.py     # Cross-chain logic
│   └── usdc_validator.py    # Validation utilities
├── tests/              # Test files
├── scripts/            # Utility scripts
└── docs/              # Documentation
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **1inch Network** - For the original cross-chain swap implementation
- **OpenZeppelin** - For secure smart contract libraries
- **XRPL Foundation** - For XRPL integration libraries
- **Ethereum Foundation** - For Web3 tools and infrastructure

---

**⚠️ Disclaimer**: This is experimental software. Use at your own risk and never use with funds you cannot afford to lose. Always test thoroughly on testnets before using on mainnet. 