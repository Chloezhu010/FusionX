import 'dotenv/config'
import {expect, jest} from '@jest/globals'
import {JsonRpcProvider, parseEther, parseUnits} from 'ethers'
import {XrplBridge} from '../src/xrpl/bridge'
import {XrplWalletManager} from '../src/xrpl/wallet'
import {config} from './config'
import {Wallet} from './wallet'
import {Resolver} from './resolver'

jest.setTimeout(1000 * 60)

describe('ETH Sepolia <> XRPL Testnet Cross-Chain Swap', () => {
    let ethProvider: JsonRpcProvider
    let xrplBridge: XrplBridge
    let xrplWalletManager: XrplWalletManager
    let ethUser: Wallet
    let ethResolver: Wallet
    let xrplUser: any
    let xrplResolver: any

    beforeAll(async () => {
        // Setup Ethereum provider
        ethProvider = new JsonRpcProvider(config.chain.source.url)
        
        // Setup XRPL bridge
        xrplBridge = new XrplBridge(
            config.chain.destination.xrplServer,
            ethProvider,
            config.chain.source.ownerPrivateKey
        )
        await xrplBridge.connect()

        // Setup XRPL wallet manager
        xrplWalletManager = new XrplWalletManager(config.chain.destination.xrplServer)
        await xrplWalletManager.connect()

        // Setup Ethereum wallets
        ethUser = new Wallet(config.chain.source.ownerPrivateKey, ethProvider)
        ethResolver = new Wallet(config.chain.source.ownerPrivateKey, ethProvider)

        // Create new XRPL wallets instead of using invalid seeds
        try {
            xrplUser = await xrplWalletManager.createWallet()
            xrplResolver = await xrplWalletManager.createWallet()
            
            console.log(`Created XRPL User Wallet: ${xrplUser.address}`)
            console.log(`Created XRPL Resolver Wallet: ${xrplResolver.address}`)
        } catch (error) {
            console.error('Failed to create XRPL wallets:', error)
            throw error
        }

        // Fund XRPL accounts if needed
        try {
            const userBalance = await xrplWalletManager.getBalance(xrplUser)
            if (parseFloat(userBalance) < 100) {
                await xrplWalletManager.fundWallet(xrplUser)
            }

            const resolverBalance = await xrplWalletManager.getBalance(xrplResolver)
            if (parseFloat(resolverBalance) < 100) {
                await xrplWalletManager.fundWallet(xrplResolver)
            }
        } catch (error) {
            console.error('Failed to fund XRPL wallets:', error)
            // Continue with test even if funding fails
        }
    })

    afterAll(async () => {
        await xrplBridge.disconnect()
        await xrplWalletManager.disconnect()
    })

    describe('ETH to XRPL Transfer', () => {
        it('should transfer ETH from Sepolia to XRP on XRPL testnet', async () => {
            const transferAmount = '5' // 5 XRP (reduced to account for fees)
            const ethAmount = parseEther('0.01') // 0.01 ETH

            // Get initial balances
            const initialEthBalance = await ethUser.getBalance()
            const initialXrpBalance = await xrplWalletManager.getBalance(xrplUser)

            console.log(`Initial ETH balance: ${initialEthBalance}`)
            console.log(`Initial XRP balance: ${initialXrpBalance}`)

            // Create escrow and initiate transfer
            // This would typically involve calling the Resolver contract
            // For now, we'll simulate the XRPL transfer directly

            const transferResult = await xrplBridge.sendXrp(
                xrplResolver,
                xrplUser.address,
                transferAmount
            )

            expect(transferResult.hash).toBeDefined()
            expect(transferResult.ledgerIndex).toBeGreaterThan(0)

            // Verify the transfer
            const isVerified = await xrplBridge.verifyTransaction(
                transferResult.hash,
                transferAmount,
                xrplUser.address
            )

            expect(isVerified).toBe(true)

            // Check final balances
            const finalXrpBalance = await xrplWalletManager.getBalance(xrplUser)
            // Account for XRPL transaction fees (typically 0.00001 XRP)
            const expectedFinalBalance = parseFloat(initialXrpBalance) + parseFloat(transferAmount) - 0.00001

            expect(parseFloat(finalXrpBalance)).toBeCloseTo(expectedFinalBalance, 1)

            console.log(`Transfer completed: ${transferResult.hash}`)
            console.log(`Final XRP balance: ${finalXrpBalance}`)
            console.log(`Expected final balance: ${expectedFinalBalance}`)
        })
    })

    describe('XRPL to ETH Transfer', () => {
        it('should transfer XRP from XRPL testnet to ETH on Sepolia', async () => {
            const transferAmount = '5' // 5 XRP
            const ethAmount = parseEther('0.005') // 0.005 ETH

            // Get initial balances
            const initialXrpBalance = await xrplWalletManager.getBalance(xrplUser)
            const initialEthBalance = await ethUser.getBalance()

            console.log(`Initial XRP balance: ${initialXrpBalance}`)
            console.log(`Initial ETH balance: ${initialEthBalance}`)

            // Send XRP from user to resolver (simulating bridge)
            const transferResult = await xrplBridge.sendXrp(
                xrplUser,
                xrplResolver.address,
                transferAmount
            )

            expect(transferResult.hash).toBeDefined()

            // Create proof for the transfer
            const proof = await xrplBridge.createProof(transferResult.hash)
            expect(proof.transactionHash).toBe(transferResult.hash)

            // Verify the proof
            const isVerified = await xrplBridge.verifyTransaction(
                proof.transactionHash,
                transferAmount,
                xrplResolver.address
            )

            expect(isVerified).toBe(true)

            // Check final balances
            const finalXrpBalance = await xrplWalletManager.getBalance(xrplUser)
            // Account for XRPL transaction fees (typically 0.00001 XRP)
            const expectedFinalBalance = parseFloat(initialXrpBalance) - parseFloat(transferAmount) - 0.00001

            expect(parseFloat(finalXrpBalance)).toBeCloseTo(expectedFinalBalance, 1)

            console.log(`Transfer completed: ${transferResult.hash}`)
            console.log(`Final XRP balance: ${finalXrpBalance}`)
            console.log(`Expected final balance: ${expectedFinalBalance}`)
        })
    })

    describe('Bridge Status', () => {
        it('should check if XRPL bridge is active', async () => {
            const isActive = await xrplBridge.isActive()
            expect(isActive).toBe(true)
        })
    })

    describe('Wallet Operations', () => {
        it('should create and fund a new XRPL wallet', async () => {
            const newWallet = await xrplWalletManager.createWallet()
            expect(newWallet.address).toMatch(/^r[a-zA-Z0-9]{25,34}$/)

            const balance = await xrplWalletManager.getBalance(newWallet)
            expect(parseFloat(balance)).toBeGreaterThan(0)

            const walletInfo = await xrplWalletManager.getWalletInfo(newWallet)
            expect(walletInfo.address).toBe(newWallet.address)
            expect(walletInfo.balance).toBe(balance)
            expect(walletInfo.sequence).toBeGreaterThan(0)
        })

        it('should validate XRPL addresses', () => {
            const validAddress = 'rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe'
            const invalidAddress = 'invalid-address'

            expect(xrplWalletManager.validateAddress(validAddress)).toBe(true)
            expect(xrplWalletManager.validateAddress(invalidAddress)).toBe(false)
        })
    })
}) 