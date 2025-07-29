import { Client, Wallet as XrplWallet } from 'xrpl'
import { dropsToXrp, xrpToDrops } from 'xrpl'
import { JsonRpcProvider, Wallet } from 'ethers'

export interface XrplTransferData {
    destination: string
    amount: string
    currency: string
    issuer?: string
}

export interface XrplProof {
    transactionHash: string
    ledgerIndex: number
    timestamp: number
    signature: string
}

export class XrplBridge {
    private client: Client
    private ethereumProvider: JsonRpcProvider
    private ethereumWallet: Wallet

    constructor(
        xrplServer: string,
        ethereumProvider: JsonRpcProvider,
        ethereumPrivateKey: string
    ) {
        this.client = new Client(xrplServer)
        this.ethereumProvider = ethereumProvider
        this.ethereumWallet = new Wallet(ethereumPrivateKey, ethereumProvider)
    }

    /**
     * Initialize XRPL connection
     */
    async connect(): Promise<void> {
        await this.client.connect()
        console.log('Connected to XRPL testnet')
    }

    /**
     * Disconnect from XRPL
     */
    async disconnect(): Promise<void> {
        await this.client.disconnect()
        console.log('Disconnected from XRPL testnet')
    }

    /**
     * Fund XRPL account from faucet
     */
    async fundAccount(address: string): Promise<void> {
        try {
            const fundResponse = await this.client.fundWallet()
            console.log(`Funded XRPL account: ${fundResponse.wallet.address}`)
        } catch (error) {
            console.error('Failed to fund XRPL account:', error)
            throw error
        }
    }

    /**
     * Get XRPL account balance
     */
    async getBalance(address: string): Promise<string> {
        try {
            const response = await this.client.request({
                command: 'account_info',
                account: address,
                ledger_index: 'validated'
            })
            
            const balance = response.result.account_data.Balance
            return dropsToXrp(balance)
        } catch (error) {
            console.error('Failed to get XRPL balance:', error)
            throw error
        }
    }

    /**
     * Send XRP from one account to another
     */
    async sendXrp(
        fromWallet: XrplWallet,
        toAddress: string,
        amount: string
    ): Promise<{ hash: string; ledgerIndex: number }> {
        try {
            const prepared = await this.client.autofill({
                TransactionType: 'Payment',
                Account: fromWallet.address,
                Amount: xrpToDrops(amount),
                Destination: toAddress
            })

            const signed = fromWallet.sign(prepared)
            const result = await this.client.submitAndWait(signed.tx_blob)

            return {
                hash: result.result.hash,
                ledgerIndex: result.result.ledger_index || 0
            }
        } catch (error) {
            console.error('Failed to send XRP:', error)
            throw error
        }
    }

    /**
     * Verify XRPL transaction
     */
    async verifyTransaction(
        transactionHash: string,
        expectedAmount: string,
        expectedDestination: string
    ): Promise<boolean> {
        try {
            const response = await this.client.request({
                command: 'tx',
                transaction: transactionHash
            })

            const tx = response.result as any
            const amount = dropsToXrp(tx.Amount || '0')
            const destination = tx.Destination || ''

            return amount === expectedAmount && destination === expectedDestination
        } catch (error) {
            console.error('Failed to verify XRPL transaction:', error)
            return false
        }
    }

    /**
     * Create proof for XRPL transaction
     */
    async createProof(transactionHash: string): Promise<XrplProof> {
        try {
            const response = await this.client.request({
                command: 'tx',
                transaction: transactionHash
            })

            const tx = response.result as any
            return {
                transactionHash: tx.hash || '',
                ledgerIndex: tx.ledger_index || 0,
                timestamp: tx.date || 0,
                signature: tx.TxnSignature || ''
            }
        } catch (error) {
            console.error('Failed to create XRPL proof:', error)
            throw error
        }
    }

    /**
     * Check if XRPL bridge is active
     */
    async isActive(): Promise<boolean> {
        try {
            const serverInfo = await this.client.request({
                command: 'server_info'
            })
            return serverInfo.result.info.complete_ledgers !== undefined
        } catch (error) {
            console.error('Failed to check XRPL bridge status:', error)
            return false
        }
    }
} 