# Deployment Guide: LOP and Escrow Factory Setup

This guide walks through deploying the 1inch Limit Order Protocol contracts and Escrow Factory to enable cross-chain swaps between Base Sepolia and XRP Ledger testnet.

## Prerequisites

- Foundry installed (`curl -L https://foundry.paradigm.xyz | bash && foundryup`)
- Private key with Base Sepolia ETH for deployment
- RPC URL for Base Sepolia

## Environment Setup

Create a `.env` file in the project root:

```bash
PRIVATE_KEY=0x...  # Your deployer private key
BASE_SEPOLIA_RPC=https://sepolia.base.org
ETHERSCAN_API_KEY=...  # Optional, for contract verification
```

## Step 1: Deploy Limit Order Protocol (LOP)

The LOP contracts need to be deployed first as they're dependencies for the escrow system.

### Deploy LOP Factory and Core Contracts

```bash
# Deploy the main LOP contract
forge script script/DeployLOP.s.sol:DeployLOP \
  --rpc-url $BASE_SEPOLIA_RPC \
  --broadcast \
  --verify \
  -vvv

# Note: Save the deployed LOP address from the output
```

Expected output will show:
- `LimitOrderProtocol` deployed at: `0x...`
- This address should be added to your config

## Step 2: Deploy Escrow Factory

The Escrow Factory manages the creation of escrow contracts for cross-chain swaps.

```bash
# Deploy Escrow Factory
forge script script/DeployEscrowFactory.s.sol:DeployEscrowFactory \
  --rpc-url $BASE_SEPOLIA_RPC \
  --broadcast \
  --verify \
  -vvv
```

Save the deployed `EscrowFactory` address from the output.

## Step 3: Configure Relayer

Update your relayer configuration with the deployed addresses:

### Update relayer/src/config.ts

```typescript
export const config = {
  baseSepoliaRpc: process.env.BASE_SEPOLIA_RPC || 'https://sepolia.base.org',
  escrowFactoryAddress: '0x...', // Address from Step 2
  lopAddress: '0x...', // Address from Step 1
  privateKey: process.env.PRIVATE_KEY,
  // ... other config
};
```

## Step 4: Test Event Emission

Create a test escrow to verify the relayer can detect events:

```bash
# Run the trigger event script
forge script script/TriggerEvent.s.sol:TriggerEvent \
  --rpc-url $BASE_SEPOLIA_RPC \
  --broadcast \
  -vvv
```

## Step 5: Start Relayer

```bash
cd relayer
npx ts-node src/index.ts
```

Expected output:
```
Starting relayer...
Listening for SrcEscrowCreated events on 0x...
```

## Verification Steps

1. **Check Contract Deployment**: Verify contracts on Base Sepolia explorer
2. **Test Event Listening**: Trigger an event and confirm relayer detection
3. **Validate Configuration**: Ensure all addresses are correct in relayer config

## Key Addresses (Base Sepolia)

After deployment, update these in your documentation:

- **Limit Order Protocol**: `0x...`
- **Escrow Factory**: `0x071e3Ae87D4aA62d0D7977C47248B0f9B185B96f` (current)
- **USDC Token**: `0x...` (if deploying test token)

## Troubleshooting

### Common Issues

1. **Insufficient Gas**: Increase gas limit in forge script
2. **RPC Issues**: Try alternative Base Sepolia RPC endpoints
3. **Event Not Detected**: Check contract address and ABI in relayer

### Debug Commands

```bash
# Check contract deployment
cast code <CONTRACT_ADDRESS> --rpc-url $BASE_SEPOLIA_RPC

# Check latest block
cast block latest --rpc-url $BASE_SEPOLIA_RPC

# Check event logs
cast logs --address <ESCROW_FACTORY_ADDRESS> --rpc-url $BASE_SEPOLIA_RPC
```

## Next Steps

1. Implement XRPL escrow creation in relayer
2. Add secret reveal detection on XRPL
3. Complete withdrawal mechanism on Base Sepolia
4. Test full cross-chain swap flow

## Resources

- [Base Sepolia Explorer](https://sepolia.basescan.org/)
- [1inch LOP Documentation](https://docs.1inch.io/docs/limit-order-protocol/introduction)
- [XRPL Escrow Documentation](https://xrpl.org/escrow.html)