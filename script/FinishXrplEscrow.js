const { Client, Wallet } = require('xrpl');

async function finishXrplEscrow() {
    // Configuration
    const XRPL_NODE_URL = 'wss://s.altnet.rippletest.net:51233';
    const USER_WALLET_SEED = 'sEdSmvqj4q1REqfkRcnCSDucuBMicWG';
    
    // Hardcoded secret for easy testing - matches CreateRealCrossChainOrder.s.sol
    const SECRET = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef';
    const ESCROW_OWNER = 'rfNXwvo8vyPRD7Sd1ZYkF9wVc19uwzMWnW'; // Your relayer address
    const ESCROW_SEQUENCE = null; // We'll need to find this from the EscrowCreate transaction
    
    console.log('🔓 Starting XRPL Escrow Finish Process...');
    console.log('Secret to reveal:', SECRET);
    
    const client = new Client(XRPL_NODE_URL);
    await client.connect();
    
    const userWallet = Wallet.fromSeed(USER_WALLET_SEED);
    console.log('User wallet address:', userWallet.classicAddress);
    
    try {
        // First, we need to find the escrow sequence number
        console.log('🔍 Looking for recent escrows from relayer...');
        const accountObjects = await client.request({
            command: 'account_objects',
            account: ESCROW_OWNER,
            type: 'escrow'
        });
        
        console.log('Found escrows:', accountObjects.result.account_objects);
        
        if (accountObjects.result.account_objects.length === 0) {
            console.log('❌ No escrows found');
            return;
        }
        
        // Find escrow with a Condition (hashlock) - we need one with HTLC
        const escrowsWithCondition = accountObjects.result.account_objects.filter(e => e.Condition);
        
        if (escrowsWithCondition.length === 0) {
            console.log('❌ No escrows with hashlock condition found');
            console.log('💡 Make sure you created an escrow with the correct hashlock');
            return;
        }
        
        // Get the most recent escrow with condition
        const escrow = escrowsWithCondition[0];
        console.log('📋 Escrow details:', escrow);
        
        // Prepare EscrowFinish transaction
        // Create proper XRPL fulfillment format: A0 22 80 20 [32-byte preimage]
        const secretBytes = SECRET.slice(2).toUpperCase(); // Remove 0x prefix
        const fulfillment = 'A0228020' + secretBytes;
        
        const escrowFinishTx = {
            TransactionType: 'EscrowFinish',
            Account: userWallet.classicAddress,
            Owner: ESCROW_OWNER,
            OfferSequence: escrow.PreviousTxnLgrSeq, // This might need adjustment
            Condition: escrow.Condition, // Required: the hashlock condition
            Fulfillment: fulfillment // Required: the secret in proper XRPL format
        };
        
        console.log('🔑 Using hashlock condition:', escrow.Condition);
        console.log('🗝️  Revealing secret:', SECRET);
        
        console.log('🔓 Submitting EscrowFinish transaction...');
        console.log('Transaction:', escrowFinishTx);
        
        const prepared = await client.autofill(escrowFinishTx);
        const signed = userWallet.sign(prepared);
        const result = await client.submitAndWait(signed.tx_blob);
        
        console.log('✅ EscrowFinish result:', result);
        
        if (result.result.meta.TransactionResult === 'tesSUCCESS') {
            console.log('🎉 SUCCESS! XRP claimed and secret revealed!');
            console.log('💰 XRP should now be in user wallet');
            console.log('🔑 Secret is now public on XRPL blockchain');
            console.log('📡 Relayer can now extract secret and claim USDC on EVM side');
        } else {
            console.log('❌ Transaction failed:', result.result.meta.TransactionResult);
        }
        
    } catch (error) {
        console.error('❌ Error finishing escrow:', error);
        
        // If sequence lookup fails, provide manual instructions
        console.log('\n📖 Manual Instructions:');
        console.log('1. Find your escrow sequence from the EscrowCreate transaction');
        console.log('2. Update ESCROW_SEQUENCE in this script');
        console.log('3. Run again with correct sequence number');
    }
    
    await client.disconnect();
}

// Run the function
finishXrplEscrow().catch(console.error);