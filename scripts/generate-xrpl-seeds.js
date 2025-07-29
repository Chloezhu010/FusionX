#!/usr/bin/env node

const { Client, Wallet } = require('xrpl');

async function generateXrplSeeds() {
    console.log('🔑 Generating XRPL Testnet Seeds\n');

    try {
        // Connect to XRPL testnet
        const client = new Client('wss://s.altnet.rippletest.net:51233');
        await client.connect();
        console.log('✅ Connected to XRPL testnet\n');

        // Generate 5 test wallets
        for (let i = 0; i < 5; i++) {
            const fundResponse = await client.fundWallet();
            const wallet = fundResponse.wallet;
            
            console.log(`Account ${i + 1}:`);
            console.log(`  Address: ${wallet.address}`);
            console.log(`  Seed: ${wallet.seed}`);
            console.log(`  Public Key: ${wallet.publicKey}`);
            console.log('');
        }

        await client.disconnect();
        console.log('📝 Usage:');
        console.log('1. Copy the seeds above to your .env file');
        console.log('2. Use them as XRPL_USER_SEED and XRPL_RESOLVER_SEED');
        console.log('3. These accounts are already funded with testnet XRP');
        console.log('');
        console.log('💡 Note: These are testnet seeds only - never use on mainnet!');

    } catch (error) {
        console.error('❌ Failed to generate XRPL seeds:', error.message);
        process.exit(1);
    }
}

generateXrplSeeds(); 