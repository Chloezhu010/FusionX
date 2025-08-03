# FusionX: Base Sepolia ↔ XRPL Cross-Chain Atomic Swap

This project implements **cross-chain atomic swaps** between Base Sepolia testnet and XRPL testnet using **Hash Time-Locked Contracts (HTLC)** with escrow contracts and crypto-conditions for trustless cross-chain swaps.

## 🏆 Hackathon Implementation

**Extend Fusion+ to XRP Ledger** - Built for the 1inch hackathon requirement to enable swaps between Ethereum and XRP Ledger while preserving hashlock and timelock functionality.

### ✅ Features Implemented
- **Bidirectional swaps**: Base Sepolia USDC ↔ XRPL XRP  
- **Hash Time-Locked Contracts (HTLC)**: Atomic swap security using secrets and hashlocks
- **Real escrow contracts**: Deployed on Base Sepolia with locked USDC
- **XRPL crypto-conditions**: Proper five-bells-condition implementation
- **Relayer service**: Automated cross-chain escrow creation
- **Secret revelation**: Complete atomic swap cycle with withdrawal

## 🚀 Quick Start

### Prerequisites

- **Node.js >= 22**
- **Foundry** (for Solidity compilation)
- **XRPL testnet account** with funded XRP
- **Base Sepolia testnet** ETH and USDC
- **five-bells-condition** library for XRPL crypto-conditions

### Installation

1. **Install dependencies:**
```bash
pnpm install
```

2. **Install required packages:**
```bash
# XRPL SDK for XRPL integration
pnpm add xrpl

# Crypto-conditions for HTLC on XRPL
npm install five-bells-condition

# Ethers.js for Ethereum interaction
npm install ethers dotenv
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
# Base Sepolia Configuration
BASE_SEPOLIA_RPC=https://sepolia.base.org
PRIVATE_KEY=your_base_sepolia_private_key

# XRPL Testnet Configuration
DST_CHAIN_RPC=wss://s.altnet.rippletest.net:51233
DST_CHAIN_CREATE_FORK=false
DST_CHAIN_PRIVATE_KEY=your_xrpl_private_key

# XRPL Test Accounts (seeds)
XRPL_USER_SEED=s...
XRPL_RESOLVER_SEED=s...
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

## 📋 Configuration

### Chain Configuration

**Base Sepolia:**
- Chain ID: 84532
- RPC: https://sepolia.base.org
- Explorer: https://sepolia.basescan.org
- Native: ETH (18 decimals)
- USDC: Available on Base Sepolia

**XRPL Testnet:**
- Server: wss://s.altnet.rippletest.net:51233
- Faucet: https://faucet.altnet.rippletest.net/accounts
- Explorer: https://testnet.xrpl.org
- Native: XRP (6 decimals)

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BASE_SEPOLIA_RPC` | Base Sepolia RPC URL | `https://sepolia.base.org` |
| `DST_CHAIN_RPC` | XRPL testnet WebSocket URL | `wss://s.altnet.rippletest.net:51233` |
| `PRIVATE_KEY` | Base Sepolia private key | `0xac...` |
| `DST_CHAIN_PRIVATE_KEY` | XRPL private key | `0x5d...` |
| `XRPL_USER_SEED` | XRPL user wallet seed | `sEdT...` |
| `XRPL_RESOLVER_SEED` | XRPL resolver wallet seed | `sEdTM...` |

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
BASE_SEPOLIA_RPC=https://sepolia.base.org
DST_CHAIN_RPC=wss://s.altnet.rippletest.net:51233
PRIVATE_KEY=your_base_sepolia_private_key
DST_CHAIN_PRIVATE_KEY=your_xrpl_private_key
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
