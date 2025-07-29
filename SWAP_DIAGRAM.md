# FusionX Cross-Chain USDC Swap Flow

## Overview
FusionX enables secure cross-chain USDC swaps between Ethereum and XRPL using atomic escrow contracts and oracle verification.

## System Architecture

```mermaid
graph TB
    subgraph "Ethereum Network"
        ETH[ETH User<br/>0x95d94e5370D9C2522dd6a4D7E670f3EC582643b1]
        USDC[USDC Token<br/>0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238]
        ESCROW[Escrow Contract<br/>0x3F2eed3D9B8E7DCCAdF6129FE39e78e0EB3e86f2]
        ORACLE[Mock XRPL Oracle<br/>0xCCC55931f5036EDDC46507342749aBF7e56d28dd]
    end
    
    subgraph "XRPL Network"
        XRPL[XRPL User<br/>rDWVLTo47HuGhrj4Tpdb9gMyZ8gGHrqniv]
        XRPL_USDC[XRPL USDC<br/>Issuer: rHuGNhqTG32mfmAvWA8hUyWRLV3tCSwKQt]
    end
    
    subgraph "Resolver Service"
        RESOLVER[Cross-Chain Resolver<br/>0x95d94e5370D9C2522dd6a4D7E670f3EC582643b1]
    end
    
    ETH -->|1. Approve USDC| USDC
    ETH -->|2. Create Escrow| ESCROW
    ESCROW -->|3. Lock USDC| USDC
    RESOLVER -->|4. Send XRPL USDC| XRPL
    RESOLVER -->|5. Verify Payment| ORACLE
    ORACLE -->|6. Confirm Payment| ESCROW
    ESCROW -->|7. Release ETH USDC| RESOLVER
```

## Detailed Swap Flow

### Phase 1: Setup & Escrow Creation
```mermaid
sequenceDiagram
    participant ETH as ETH User
    participant USDC as USDC Contract
    participant ESCROW as Escrow Contract
    participant RESOLVER as Resolver
    
    ETH->>USDC: 1. Approve 0.2 USDC for Escrow
    Note over ETH,USDC: Transaction: 1735791bf7191d5ed713782a76008bc1d0fc0e9b51580d5d0eec62210f169eeb
    
    ETH->>ESCROW: 2. Create Escrow (0.2 USDC)
    Note over ETH,ESCROW: Order Hash: 9edbff5e03ab3493b7f2f3240ee3894c7262818959a090c6ed1b58314dd2d907
    ESCROW->>USDC: 3. Transfer USDC to Escrow
    Note over ESCROW,USDC: Transaction: 39492faeccfb4810277e5b1644fb9700e3393a79ddb9f36803654e8d83f3af47
    
    ESCROW->>ESCROW: 4. Store Escrow Data
    Note over ESCROW: - Maker: ETH User<br/>- Taker: Resolver<br/>- Amount: 200,000 units<br/>- Hashlock: 8271e2206130ba8451bef8780cdd26e065429e3fdd5a259c3d2d6400999fea8d<br/>- Timelocks: 15s withdrawal, 60s cancellation
```

### Phase 2: XRPL Payment & Verification
```mermaid
sequenceDiagram
    participant RESOLVER as Resolver
    participant XRPL as XRPL User
    participant XRPL_USDC as XRPL USDC
    participant ORACLE as Mock Oracle
    
    RESOLVER->>XRPL: 5. Send 0.198000 USDC
    Note over RESOLVER,XRPL: Simulated Transaction: FA373263E4D7A1FA72A3907E7490E94F89D37AF0E37F932A12DEE1552ECFC22D
    
    XRPL->>XRPL_USDC: 6. Transfer XRPL USDC
    Note over XRPL,XRPL_USDC: Amount: 0.198000 USDC<br/>Destination: rDWVLTo47HuGhrj4Tpdb9gMyZ8gGHrqniv
    
    RESOLVER->>ORACLE: 7. Verify XRPL Payment
    Note over RESOLVER,ORACLE: - TX Hash: FA373263E4D7A1FA72A3907E7490E94F89D37AF0E37F932A12DEE1552ECFC22D<br/>- Secret: a180a2ac2e0a0acaf750a9a60e5fcdc8658a51037054ee5cb287fe83f3796721<br/>- Destination: rDWVLTo47HuGhrj4Tpdb9gMyZ8gGHrqniv<br/>- Amount: 0.198000
    
    ORACLE->>RESOLVER: 8. Payment Verified ✅
    Note over ORACLE,RESOLVER: Mock Oracle always returns true
```

### Phase 3: Withdrawal & Completion
```mermaid
sequenceDiagram
    participant RESOLVER as Resolver
    participant ESCROW as Escrow Contract
    participant USDC as USDC Contract
    participant ETH as ETH User
    
    Note over RESOLVER: Wait for timelock (15 seconds)
    
    RESOLVER->>ESCROW: 9. Withdraw with Secret
    Note over RESOLVER,ESCROW: - Secret: a180a2ac2e0a0acaf750a9a60e5fcdc8658a51037054ee5cb287fe83f3796721<br/>- Order Hash: 9edbff5e03ab3493b7f2f3240ee3894c7262818959a090c6ed1b58314dd2d907<br/>- XRPL TX: FA373263E4D7A1FA72A3907E7490E94F89D37AF0E37F932A12DEE1552ECFC22D
    
    ESCROW->>ESCROW: 10. Verify Conditions
    Note over ESCROW: ✅ Taker matches<br/>✅ Secret matches<br/>✅ Timelock expired<br/>✅ Oracle verified payment<br/>✅ Not already completed
    
    ESCROW->>USDC: 11. Transfer USDC to Resolver
    Note over ESCROW,USDC: Transaction: ab5f00e3ed193dfa3c01851956828274ce77fa1bbdbd8a85e08779b2ecec5d76
    
    USDC->>RESOLVER: 12. Receive 0.2 USDC
    Note over USDC,RESOLVER: Resolver now has the ETH USDC
```

## Security Features

### 🔒 Atomic Escrow
- **Hashlock**: Uses cryptographic hash of secret for atomicity
- **Timelocks**: Prevents indefinite locking of funds
- **Oracle Verification**: Ensures XRPL payment actually occurred

### ⏰ Timelock Structure
```
┌─────────────────────────────────────────────────────────────┐
│                    TIMELOCK WINDOWS                        │
├─────────────────────────────────────────────────────────────┤
│ T=0s    T=15s   T=60s                                     │
│   │       │       │                                        │
│   ▼       ▼       ▼                                        │
│ [Escrow] [Withdraw] [Cancel]                              │
│ Created   Window    Window                                 │
└─────────────────────────────────────────────────────────────┘
```

### 🔐 Oracle Security
```mermaid
graph LR
    A[XRPL Transaction] --> B[Oracle Monitor]
    B --> C[Verify Payment Details]
    C --> D[Report to Ethereum]
    D --> E[Escrow Contract]
    E --> F[Allow/Deny Withdrawal]
```

## Current Implementation Details

### ✅ Working Components
- **ETH Escrow Creation**: ✅ Secure locking of USDC
- **XRPL Payment Simulation**: ✅ Simulated cross-chain transfer
- **Oracle Verification**: ✅ Mock oracle for testing
- **Timelock Management**: ✅ Proper time-based security
- **Withdrawal Process**: ✅ Secure fund release

### 🎭 Demo Mode Features
- **Simulated XRPL Payments**: Fake transaction hashes for testing
- **Mock Oracle**: Always returns `true` for verification
- **Testnet USDC**: Using Sepolia testnet tokens

### 📊 Transaction Summary
| Step | Transaction Hash | Status | Gas Used |
|------|-----------------|--------|----------|
| USDC Approval | `1735791bf7191d5ed713782a76008bc1d0fc0e9b51580d5d0eec62210f169eeb` | ✅ | 55,437 |
| Escrow Creation | `39492faeccfb4810277e5b1644fb9700e3393a79ddb9f36803654e8d83f3af47` | ✅ | 488,081 |
| XRPL Payment | `FA373263E4D7A1FA72A3907E7490E94F89D37AF0E37F932A12DEE1552ECFC22D` | ✅ | Simulated |
| Withdrawal | `ab5f00e3ed193dfa3c01851956828274ce77fa1bbdbd8a85e08779b2ecec5d76` | ✅ | 134,527 |

## Production Considerations

### 🔄 Real-World Implementation
1. **Replace Mock Oracle** with real XRPL oracle
2. **Use Real XRPL Transactions** instead of simulations
3. **Add Multi-Sig Security** for oracle consensus
4. **Deploy to Mainnet** with real USDC contracts

### 🛡️ Additional Security
- **Multi-Oracle Consensus**: Multiple oracles vote on payment verification
- **Light Client Verification**: Direct cryptographic proof verification
- **Insurance Mechanisms**: Coverage for failed swaps
- **Dispute Resolution**: Arbitration for contested transactions

---

*This diagram shows the current working implementation of FusionX cross-chain USDC swaps between Ethereum and XRPL networks.* 