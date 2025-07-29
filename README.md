# ETH Sepolia ↔ XRPL Testnet Cross-Chain Swap

A cross-chain swap implementation that enables asset transfers between Ethereum Sepolia testnet and XRPL testnet, using 1inch's Limit Order Protocol (LOP) for real market exchange rates.

## Features

- **Cross-Chain Transfers**: ETH ↔ XRP swaps between Ethereum Sepolia and XRPL testnet
- **Real Market Rates**: Integration with 1inch's Limit Order Protocol for accurate exchange rates
- **Fallback Rates**: Hardcoded rates when LOP is unavailable
- **XRPL Integration**: Direct interaction with XRPL testnet
- **Proof Generation**: Cryptographic proofs for cross-chain verification
- **Rate Caching**: Performance optimization with 1-minute rate caching

## Architecture

### Exchange Rate Sources (Priority Order)

1. **1inch Limit Order Protocol (LOP)** - Primary source for real market rates
2. **Hardcoded Rates** - Fallback when LOP is unavailable
3. **Rate Caching** - 1-minute cache for performance

### Cross-Chain Flow

```
ETH Sepolia → XRPL Testnet:
1. User initiates swap on Ethereum
2. Resolver contract creates escrow
3. LOP provides real market rate
4. XRPL bridge executes transfer
5. User receives XRP on XRPL

XRPL Testnet → ETH Sepolia:
1. User sends XRP to resolver
2. Proof generated for XRPL transaction
3. Resolver verifies proof on Ethereum
4. User receives ETH on Sepolia
```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd new_FusionX

# Install dependencies
pnpm install

# Install XRPL SDK
pnpm add xrpl

# Build contracts
pnpm run build
```

## Configuration

Create a `.env` file with the following variables:

```env
# Ethereum Sepolia
SRC_CHAIN_RPC=https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY
SRC_CHAIN_PRIVATE_KEY=your_ethereum_private_key

# XRPL Testnet
DST_CHAIN_RPC=wss://s.altnet.rippletest.net:51233
DST_CHAIN_PRIVATE_KEY=your_xrpl_private_key

# Optional: XRPL Seeds (for testing)
XRPL_USER_SEED=your_xrpl_user_seed
XRPL_RESOLVER_SEED=your_xrpl_resolver_seed
```

### LOP Configuration

The system automatically integrates with 1inch's Limit Order Protocol:

```typescript
// LOP contract addresses (mainnet)
const LOP_ADDRESSES = {
  ETHEREUM: '0x111111125421ca6dc452d289314280a0f8842a65',
  BSC: '0x111111125421ca6dc452d289314280a0f8842a65',
  // Add more chains as needed
}
```

## Usage

### Running Tests

```bash
# Run all tests
pnpm test

# Run specific test file
pnpm test tests/eth-xrpl.spec.ts

# Run with specific environment variables
SRC_CHAIN_RPC=https://eth.merkle.io DST_CHAIN_RPC=wss://s.altnet.rippletest.net:51233 pnpm test
```

### Exchange Rate Calculation

```typescript
import { XrplBridge } from './src/xrpl/bridge'

const bridge = new XrplBridge(
  'wss://s.altnet.rippletest.net:51233',
  provider,
  privateKey,
  lopAddress,
  lopABI
)

// Get real market rate from LOP
const rate = await bridge.calculateExchangeRate('ETH', 'XRP')
console.log(`1 ETH = ${rate} XRP`)

// Calculate destination amount
const ethAmount = parseEther('0.01')
const xrpAmount = await bridge.calculateDestinationAmount(
  ethAmount,
  'ETH',
  'XRP'
)
```

## Exchange Rate Sources

### 1. 1inch Limit Order Protocol (Primary)

The system prioritizes real market rates from 1inch's LOP:

```typescript
// LOP provides real-time market rates
const lopRate = await lopIntegration.getMarketRate('ETH', 'USDC')
// Example: 1 ETH = 2500 USDC (real market rate)
```

### 2. Hardcoded Rates (Fallback)

When LOP is unavailable, the system uses hardcoded rates:

```typescript
const rates = {
  'ETH': { 'XRP': 1800, 'USDC': 2500 },
  'USDC': { 'XRP': 0.72, 'ETH': 0.0004 },
  'XRP': { 'ETH': 0.00056, 'USDC': 1.39 }
}
```

### 3. Rate Caching

Rates are cached for 1 minute to improve performance:

```typescript
// First call: fetches from LOP
const rate1 = await bridge.calculateExchangeRate('ETH', 'XRP')

// Second call within 1 minute: uses cache
const rate2 = await bridge.calculateExchangeRate('ETH', 'XRP')
// rate1 === rate2 (cached)
```

## API Reference

### XrplBridge Class

```typescript
class XrplBridge {
  // Calculate exchange rate (LOP + fallback)
  calculateExchangeRate(sourceToken: string, destinationToken: string): Promise<number>
  
  // Calculate destination amount with fees
  calculateDestinationAmount(sourceAmount: bigint, sourceToken: string, destinationToken: string): Promise<bigint>
  
  // Execute XRPL transfer
  sendXrp(fromWallet: XrplWallet, toAddress: string, amount: string): Promise<{hash: string, ledgerIndex: number}>
  
  // Verify XRPL transaction
  verifyTransaction(transactionHash: string, expectedAmount: string, expectedDestination: string): Promise<boolean>
  
  // Create proof for cross-chain verification
  createProof(transactionHash: string): Promise<XrplProof>
}
```

### LOPIntegration Class

```typescript
class LOPIntegration {
  // Get best quote from LOP
  getBestQuote(sourceToken: string, targetToken: string, amount: bigint): Promise<LOPQuote | null>
  
  // Execute LOP order
  executeQuote(quote: LOPQuote, wallet: Wallet): Promise<{success: boolean, txHash?: string}>
  
  // Get market rate from LOP
  getMarketRate(sourceToken: string, targetToken: string): Promise<number>
}
```

## Testing

### Test Structure

```bash
tests/
├── eth-xrpl.spec.ts          # Main cross-chain tests
├── config.ts                  # Test configuration
├── wallet.ts                  # Ethereum wallet utilities
└── escrow-factory.ts         # Escrow factory utilities
```

### Running Specific Tests

```bash
# Test exchange rate calculations
pnpm test -- --testNamePattern="Exchange Rate Calculations"

# Test LOP integration
pnpm test -- --testNamePattern="LOP Integration"

# Test XRPL transfers
pnpm test -- --testNamePattern="ETH to XRPL Transfer"
```

## Troubleshooting

### Common Issues

1. **LOP Rate Unavailable**
   ```
   Warning: LOP rate not available, falling back to hardcoded rates
   ```
   - Check LOP contract address
   - Verify network connectivity
   - Ensure token addresses are correct

2. **XRPL Connection Failed**
   ```
   Error: Failed to connect to XRPL testnet
   ```
   - Check XRPL server URL
   - Verify network connectivity
   - Try alternative XRPL testnet endpoints

3. **Rate Cache Issues**
   ```
   Error: Exchange rate not available
   ```
   - Clear rate cache
   - Check token symbol mapping
   - Verify fallback rates are configured

### Debug Mode

Enable debug logging:

```typescript
// In your test or application
process.env.DEBUG = 'xrpl:bridge,lop:integration'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
