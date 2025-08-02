const { Client, Wallet } = require('xrpl');

async function finishXrplEscrow() {
    // Configuration
    const XRPL_NODE_URL = 'wss://s.altnet.rippletest.net:51233';
    const USER_WALLET_SEED = 'sEdSmvqj4q1REqfkRcnCSDucuBMicWG';
    
    // Hardcoded secret for easy testing - matches CreateRealCrossChainOrder.s.sol
    const SECRET = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef';
    const ESCROW_OWNER = 'rfNXwvo8vyPRD7Sd1ZYkF9wVc19uwzMWnW'; // Your relayer address
    
    // console.log('🔓 Starting XRPL Escrow Finish Process...');
    // console.log('Secret to reveal:', SECRET);
    
    const client = new Client(XRPL_NODE_URL);
    await client.connect();
    
    // const userWallet = Wallet.fromSeed(USER_WALLET_SEED);
    // console.log('User wallet address:', userWallet.classicAddress);
    
    // 1. Read escrow from XRPL
    // console.log('🔍 Looking for recent escrows from relayer...');
    const accountObjects = await client.request({
        command: 'account_objects',
        account: ESCROW_OWNER,
        type: 'escrow'
    });
    
    console.log('Found escrows:', JSON.stringify(accountObjects.result.account_objects, null, 2));
    
    if (accountObjects.result.account_objects.length === 0) {
        console.log('❌ No escrows found');
        await client.disconnect();
        return;
    }
    
    const escrowsWithCondition = accountObjects.result.account_objects.filter(e => e.Condition);
    const escrow = escrowsWithCondition[0];
    
    if (!escrow) {
        console.log('❌ No escrows with hashlock condition found');
        await client.disconnect();
        return;
    }

// 2. CHECK IF ESCROW HAS CRYPTO-CONDITION
if (escrow.Condition) {
    // 3. HASH OUR SECRET
    const crypto = require('crypto');
    const secretBuffer = Buffer.from(SECRET.slice(2), 'hex');
    const ourHashlock = '0x' + crypto.createHash('sha3-256').update(secretBuffer).digest('hex');
    
    // 4. COMPARE WITH ESCROW CONDITION
    const escrowCondition = '0x' + escrow.Condition.toLowerCase();
    
    if (ourHashlock.toLowerCase() === escrowCondition.toLowerCase()) {
        // ✅ SECRET IS CORRECT - proceed with crypto-condition escrow
        const escrowFinishTx = {
            TransactionType: 'EscrowFinish',
            Account: userWallet.classicAddress,
            Owner: ESCROW_OWNER,
            OfferSequence: escrow.PreviousTxnLgrSeq,
            Condition: escrow.Condition,
            Fulfillment: SECRET.slice(2).toUpperCase() // Original secret
        };
    console.log('🔓 Submitting EscrowFinish transaction to withdraw XRP...');
    const prepared = await client.autofill(escrowFinishTx);
    const signed = userWallet.sign(prepared);
    const result = await client.submitAndWait(signed.tx_blob);
    
    console.log('✅ XRP Withdrawal Result:', result);
    
    if (result.result.meta.TransactionResult === 'tesSUCCESS') {
        console.log('🎉 SUCCESS! XRP withdrawn and secret revealed!');
    }
    } else {
        // ❌ SECRET IS WRONG - cannot proceed
        console.log('Wrong secret!');
        return;
    }
    } else {
        // Time-locked escrow (current code handles this)
    }
    
    await client.disconnect();
}

// Run the function
finishXrplEscrow().catch(console.error);