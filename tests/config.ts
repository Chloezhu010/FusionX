import {z} from 'zod'
import Sdk from '@1inch/cross-chain-sdk'

const bool = z
    .string()
    .transform((v) => v.toLowerCase() === 'true')
    .pipe(z.boolean())

const ConfigSchema = z.object({
    SRC_CHAIN_RPC: z.string().url(),
    DST_CHAIN_RPC: z.string().url(),
    SRC_CHAIN_CREATE_FORK: bool.default('true'),
    DST_CHAIN_CREATE_FORK: bool.default('false'), // XRPL doesn't support forking
    SRC_CHAIN_PRIVATE_KEY: z.string(),
    DST_CHAIN_PRIVATE_KEY: z.string()
})

const fromEnv = ConfigSchema.parse(process.env)

export const config = {
    chain: {
        source: {
            chainId: 11155111, // Sepolia chain ID
            url: fromEnv.SRC_CHAIN_RPC,
            createFork: fromEnv.SRC_CHAIN_CREATE_FORK,
            xrplBridge: '0x111111125421ca6dc452d289314280a0f8842a65', // Replace with actual bridge address
            wrappedNative: '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9', // Sepolia WETH
            ownerPrivateKey: fromEnv.SRC_CHAIN_PRIVATE_KEY,
            tokens: {
                USDC: {
                    address: '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238', // Sepolia USDC
                    donor: '0x70997970C51812dc3A010C7d01b50e0d17dc79C8' // Test account
                }
            }
        },
        destination: {
            chainId: 'XRPL_TESTNET', // Custom XRPL testnet chain ID
            url: fromEnv.DST_CHAIN_RPC,
            createFork: false, // XRPL doesn't support forking
            xrplServer: 'wss://s.altnet.rippletest.net:51233',
            xrplBridge: '0x111111125421ca6dc452d289314280a0f8842a65', // Replace with actual bridge address
            wrappedNative: 'native', // XRP is native on XRPL
            ownerPrivateKey: fromEnv.DST_CHAIN_PRIVATE_KEY,
            tokens: {
                XRP: {
                    address: 'native', // XRP is native token
                    donor: 'rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe' // XRPL testnet faucet
                }
            }
        }
    }
} as const

export type ChainConfig = (typeof config.chain)['source' | 'destination']
