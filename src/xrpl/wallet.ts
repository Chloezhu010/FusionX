import { Client, Wallet as XrplWallet } from 'xrpl'

export class XrplWalletManager {
    private client: Client

    constructor(xrplServer: string) {
        this.client = new Client(xrplServer)
    }

    /**
     * Connect to XRPL
     */
    async connect(): Promise<void> {
        await this.client.connect()
        console.log('XRPL Wallet Manager connected')
    }

    /**
     * Disconnect from XRPL
     */
    async disconnect(): Promise<void> {
        await this.client.disconnect()
        console.log('XRPL Wallet Manager disconnected')
    }

    /**
     * Create a new XRPL wallet
     */
    async createWallet(): Promise<XrplWallet> {
        try {
            const fundResponse = await this.client.fundWallet()
            console.log(`Created XRPL wallet: ${fundResponse.wallet.address}`)
            return fundResponse.wallet
        } catch (error) {
            console.error('Failed to create XRPL wallet:', error)
            throw error
        }
    }

    /**
     * Import existing XRPL wallet from seed
     */
    importWallet(seed: string): XrplWallet {
        try {
            return XrplWallet.fromSeed(seed)
        } catch (error) {
            console.error('Failed to import XRPL wallet:', error)
            throw error
        }
    }

    /**
     * Get wallet balance
     */
    async getBalance(wallet: XrplWallet): Promise<string> {
        try {
            const response = await this.client.request({
                command: 'account_info',
                account: wallet.address,
                ledger_index: 'validated'
            })
            
            const balance = response.result.account_data.Balance
            return this.dropsToXrp(balance)
        } catch (error) {
            console.error('Failed to get wallet balance:', error)
            throw error
        }
    }

    /**
     * Fund wallet from faucet
     */
    async fundWallet(wallet: XrplWallet): Promise<void> {
        try {
            const fundResponse = await this.client.fundWallet()
            console.log(`Funded wallet: ${fundResponse.wallet.address}`)
        } catch (error) {
            console.error('Failed to fund wallet:', error)
            throw error
        }
    }

    /**
     * Convert drops to XRP
     */
    private dropsToXrp(drops: string): string {
        const dropsNum = parseInt(drops)
        return (dropsNum / 1000000).toString()
    }

    /**
     * Convert XRP to drops
     */
    private xrpToDrops(xrp: string): string {
        const xrpNum = parseFloat(xrp)
        return (xrpNum * 1000000).toString()
    }

    /**
     * Validate XRPL address
     */
    validateAddress(address: string): boolean {
        try {
            // Basic XRPL address validation
            return address.startsWith('r') && address.length === 34
        } catch (error) {
            return false
        }
    }

    /**
     * Get wallet info
     */
    async getWalletInfo(wallet: XrplWallet): Promise<{
        address: string
        balance: string
        sequence: number
    }> {
        try {
            const response = await this.client.request({
                command: 'account_info',
                account: wallet.address,
                ledger_index: 'validated'
            })
            
            const accountData = response.result.account_data
            return {
                address: wallet.address,
                balance: this.dropsToXrp(accountData.Balance),
                sequence: accountData.Sequence
            }
        } catch (error) {
            console.error('Failed to get wallet info:', error)
            throw error
        }
    }
} 