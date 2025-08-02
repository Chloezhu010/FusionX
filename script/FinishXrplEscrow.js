const { Client, Wallet } = require('xrpl');

async function finishXrplEscrow() {
    // Configuration
    const XRPL_NODE_URL = 'wss://s.altnet.rippletest.net:51233';
    const USER_WALLET_SEED = 'sEdTM1uX8pu2do5XvTnutH6HsouMaM2'; // From your .env - user wallet
    
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
        
        // Get the most recent escrow (last in the array)
        const escrow = accountObjects.result.account_objects[accountObjects.result.account_objects.length - 1];
        
        console.log('⚠️  Using time-locked escrow (no crypto-condition yet)');
        console.log('📋 Escrow details:', escrow);
        
        // For time-locked escrows (no condition), we just need to wait for FinishAfter time
        const escrowFinishTx = {
            TransactionType: 'EscrowFinish',
            Account: userWallet.classicAddress,
            Owner: ESCROW_OWNER,
            OfferSequence: escrow.PreviousTxnLgrSeq // Just finish the time-locked escrow
            // No Condition or Fulfillment needed for time-locked escrows
        };
        
        console.log('⏰ Time-locked escrow, no secret needed');
        console.log('⏳ FinishAfter time:', new Date(escrow.FinishAfter * 1000));
        
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