export interface XrplAccount {
    address: string
    seed: string
    balance: string
    sequence: number
}

export interface XrplTransaction {
    hash: string
    ledgerIndex: number
    timestamp: number
    amount: string
    destination: string
    source: string
    fee: string
}

export interface XrplTransferRequest {
    fromAddress: string
    toAddress: string
    amount: string
    currency: string
    issuer?: string
}

export interface XrplTransferResponse {
    success: boolean
    transactionHash?: string
    ledgerIndex?: number
    error?: string
}

export interface XrplProof {
    transactionHash: string
    ledgerIndex: number
    timestamp: number
    signature: string
    amount: string
    destination: string
    source: string
}

export interface XrplBridgeConfig {
    server: string
    ethereumProvider: string
    ethereumPrivateKey: string
    bridgeContract: string
}

export interface XrplTestnetConfig {
    server: string
    faucetUrl: string
    chainId: string
    nativeCurrency: {
        name: string
        symbol: string
        decimals: number
    }
}

export const XRPL_TESTNET_CONFIG: XrplTestnetConfig = {
    server: 'wss://s.altnet.rippletest.net:51233',
    faucetUrl: 'https://faucet.altnet.rippletest.net/accounts',
    chainId: 'XRPL_TESTNET',
    nativeCurrency: {
        name: 'XRP',
        symbol: 'XRP',
        decimals: 6
    }
}

export interface XrplEscrowData {
    escrowId: string
    owner: string
    destination: string
    amount: string
    cancelAfter: number
    finishAfter: number
    condition?: string
}

export interface XrplEscrowCreateRequest {
    owner: string
    destination: string
    amount: string
    cancelAfter: number
    finishAfter: number
    condition?: string
}

export interface XrplEscrowFinishRequest {
    owner: string
    escrowId: string
    condition?: string
    fulfillment?: string
}

export interface XrplEscrowCancelRequest {
    owner: string
    escrowId: string
} 