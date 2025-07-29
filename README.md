# FusionX: ETH <> XRPL Cross-Chain Swap

This project implements cross-chain swaps between Ethereum Sepolia testnet and XRPL testnet using escrow contracts and XRPL bridge functionality.

## 🚀 Quick Start

### Prerequisites

- Node.js >= 22
- Foundry (for Solidity compilation)
- XRPL testnet account

### Installation

1. **Install dependencies:**
```bash
pnpm install
```

2. **Install XRPL SDK (required for XRPL integration):**
```bash
pnpm add xrpl
```

3. **Install Foundry:**
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

4. **Install contract dependencies:**
```bash
forge install
```

### Configuration

1. **Create environment file:**
```bash
cp .env.example .env
```

2. **Update `.env` with your configuration:**
```bash
# Ethereum Sepolia Configuration
SRC_CHAIN_RPC=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
SRC_CHAIN_CREATE_FORK=true
SRC_CHAIN_PRIVATE_KEY=your_eth_private_key

# XRPL Testnet Configuration
DST_CHAIN_RPC=wss://s.altnet.rippletest.net:51233
DST_CHAIN_CREATE_FORK=false
DST_CHAIN_PRIVATE_KEY=your_xrpl_private_key

# XRPL Test Accounts (seeds)
XRPL_USER_SEED=sEdTM1uX8pu2do5XvTnutH6HsouMaM2
XRPL_RESOLVER_SEED=sEdTMMv3qB8kYz6HgfuH4sQt8tLSMv
```

### Running Tests

**ETH <> XRPL Cross-Chain Tests:**
```bash
pnpm test tests/eth-xrpl.spec.ts
```

**All Tests:**
```bash
pnpm test
```

## 🏗️ Architecture

### Core Components

1. **Resolver Contract** (`contracts/src/Resolver.sol`)
   - Handles escrow deployment and XRPL bridge calls
   - Replaces limit order protocol with XRPL bridge

2. **XRPL Bridge** (`src/xrpl/bridge.ts`)
   - Manages XRPL testnet connections
   - Handles cross-chain transfers and proofs

3. **XRPL Wallet Manager** (`src/xrpl/wallet.ts`)
   - XRPL account creation and management
   - Balance checking and funding

### Cross-Chain Flow

#### ETH → XRPL Transfer:
1. User creates escrow on Ethereum
2. Resolver calls XRPL bridge to initiate transfer
3. Bridge sends XRP to destination address
4. User can withdraw from escrow with secret

#### XRPL → ETH Transfer:
1. User sends XRP to bridge address on XRPL
2. Bridge creates proof of transfer
3. Resolver completes transfer on Ethereum
4. User receives ETH in escrow

## 🔧 Development

### Adding New Features

1. **XRPL Bridge Functions:**
   - Add methods to `src/xrpl/bridge.ts`
   - Update interface in `contracts/src/interfaces/IXrplBridge.sol`

2. **New Token Support:**
   - Update `tests/config.ts` with token addresses
   - Add token-specific logic in bridge

3. **Additional Chains:**
   - Extend configuration in `tests/config.ts`
   - Create new bridge implementation

### Testing

**Unit Tests:**
```bash
pnpm test tests/unit/
```

**Integration Tests:**
```bash
pnpm test tests/integration/
```

**XRPL Specific Tests:**
```bash
pnpm test tests/eth-xrpl.spec.ts
```

## 📋 Configuration

### Chain Configuration

**Ethereum Sepolia:**
- Chain ID: 11155111
- RPC: https://sepolia.infura.io/v3/YOUR_KEY
- WETH: 0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9
- USDC: 0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238

**XRPL Testnet:**
- Server: wss://s.altnet.rippletest.net:51233
- Faucet: https://faucet.altnet.rippletest.net/accounts
- Native: XRP (6 decimals)

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SRC_CHAIN_RPC` | Ethereum Sepolia RPC URL | `https://sepolia.infura.io/v3/...` |
| `DST_CHAIN_RPC` | XRPL testnet WebSocket URL | `wss://s.altnet.rippletest.net:51233` |
| `SRC_CHAIN_PRIVATE_KEY` | Ethereum private key | `0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80` |
| `DST_CHAIN_PRIVATE_KEY` | XRPL private key | `0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a` |
| `XRPL_USER_SEED` | XRPL user wallet seed | `sEdTM1uX8pu2do5XvTnutH6HsouMaM2` |
| `XRPL_RESOLVER_SEED` | XRPL resolver wallet seed | `sEdTMMv3qB8kYz6HgfuH4sQt8tLSMv` |

## 🚨 Important Notes

1. **XRPL Testnet**: This uses XRPL testnet, not mainnet
2. **Forking**: XRPL doesn't support forking like Ethereum
3. **Funding**: XRPL testnet accounts need funding from faucet
4. **Proofs**: All XRPL transfers require cryptographic proofs
5. **Timelocks**: Escrow timelocks are critical for security

## 🔧 Troubleshooting

### Common Issues

**1. XRPL Module Not Found Error:**
```bash
Cannot find module 'xrpl' from '../src/xrpl/wallet.ts'
```

**Solution:**
```bash
pnpm add xrpl
```

**2. TypeScript Import Errors:**
```bash
The requested module 'xrpl' does not provide an export named 'xrpl'
```

**Solution:** The import has been fixed in the code. Make sure you're using the latest version:
```bash
pnpm install
```

**3. XRPL Connection Issues:**
```bash
Failed to connect to XRPL testnet
```

**Solution:**
- Check your internet connection
- Verify the XRPL server URL: `wss://s.altnet.rippletest.net:51233`
- Try alternative testnet servers if needed

**4. Environment Variables Not Found:**
```bash
Cannot find name 'process'
```

**Solution:** Add to your `.env` file:
```bash
# Make sure all required variables are set
SRC_CHAIN_RPC=https://sepolia.infura.io/v3/YOUR_KEY
DST_CHAIN_RPC=wss://s.altnet.rippletest.net:51233
SRC_CHAIN_PRIVATE_KEY=your_eth_private_key
DST_CHAIN_PRIVATE_KEY=your_eth_private_key_for_bridge
XRPL_USER_SEED=sEdTM1uX8pu2do5XvTnutH6HsouMaM2
XRPL_RESOLVER_SEED=sEdTMMv3qB8kYz6HgfuH4sQt8tLSMv
```

**5. Test Failures:**
```bash
Test suite failed to run
```

**Solution:**
1. Install XRPL SDK: `pnpm add xrpl`
2. Build contracts: `forge build`
3. Check environment variables
4. Ensure XRPL testnet is accessible

### Getting Help

If you encounter issues not covered above:
1. Check the [XRPL Documentation](https://xrpl.org/docs/)
2. Review the test files for working examples
3. Create an issue in this repository with:
   - Error message
   - Steps to reproduce
   - Environment details

## 🔒 Security

- All private keys should be kept secure
- Use testnet accounts only
- Validate all XRPL addresses before transfers
- Verify proofs before completing transfers
- Test thoroughly before mainnet deployment

## 📞 Support

For issues and questions:
- Create an issue in this repository
- Check the test files for examples
- Review the XRPL documentation

## 📄 License

MIT License - see LICENSE file for details
