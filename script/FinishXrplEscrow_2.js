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
    
    const userWallet = Wallet.fromSeed(USER_WALLET_SEED);
    console.log('User wallet address:', userWallet.classicAddress);
    
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
    // 3. CREATE CRYPTO-CONDITION FROM SECRET (same as relayer)
    const cc = require('five-bells-condition');
    const secretBuffer = Buffer.from(SECRET.slice(2), 'hex');
    
    // Create preimage condition using same method as relayer
    const preimageCondition = new cc.PreimageSha256();
    preimageCondition.setPreimage(secretBuffer);
    
    // Generate the condition binary and encode to hex
    const conditionBinary = preimageCondition.getConditionBinary();
    const ourCondition = conditionBinary.toString('hex').toUpperCase();
    
    // 4. COMPARE WITH ESCROW CONDITION
    const escrowCondition = escrow.Condition.toUpperCase();
    console.log('Our condition:', ourCondition);
    console.log('Escrow condition:', escrowCondition);
    console.log('📋 Escrow object details:', JSON.stringify(escrow, null, 2));
    
    // Get the original EscrowCreate transaction to find the sequence number
    console.log('🔍 Looking up original EscrowCreate transaction...');
    const originalTx = await client.request({
        command: 'tx',
        transaction: escrow.PreviousTxnID
    });
    
    console.log('📜 Original EscrowCreate sequence:', originalTx.result.Sequence);
    
    // Check if FinishAfter time has passed
    const currentTime = Math.floor(Date.now() / 1000);
    const finishAfter = escrow.FinishAfter;
    console.log('⏰ Current time:', currentTime);
    console.log('⏰ FinishAfter:', finishAfter);
    console.log('⏰ Can finish now?', currentTime >= finishAfter);
    
    if (ourCondition.toLowerCase() === escrowCondition.toLowerCase()) {
        // ✅ SECRET IS CORRECT - proceed with crypto-condition escrow
        // Generate proper fulfillment using crypto-condition library
        const fulfillmentBinary = preimageCondition.serializeBinary();
        const fulfillment = fulfillmentBinary.toString('hex').toUpperCase();
        
        console.log('🔑 Fulfillment details:');
        console.log('  Fulfillment (hex):', fulfillment);
        console.log('  Fulfillment length:', fulfillment.length);
        
        const escrowFinishTx = {
            TransactionType: 'EscrowFinish',
            Account: userWallet.classicAddress,
            Owner: ESCROW_OWNER,
            OfferSequence: originalTx.result.Sequence, // Use sequence from original EscrowCreate
            Condition: escrow.Condition,
            Fulfillment: fulfillment
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