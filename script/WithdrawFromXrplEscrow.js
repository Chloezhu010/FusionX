const { Client, Wallet } = require('xrpl');

async function finishXrplEscrow() {
    // Configuration
    const XRPL_NODE_URL = 'wss://s.altnet.rippletest.net:51233';
    const USER_WALLET_SEED = 'sEdSmvqj4q1REqfkRcnCSDucuBMicWG';
    
    // Hardcoded secret for easy testing - matches CreateRealCrossChainOrder.s.sol
    const SECRET = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef';
    const ESCROW_OWNER = 'rfNXwvo8vyPRD7Sd1ZYkF9wVc19uwzMWnW'; // Your relayer address
    
    const client = new Client(XRPL_NODE_URL);
    await client.connect();
    
    const userWallet = Wallet.fromSeed(USER_WALLET_SEED);
    console.log('User wallet address:', userWallet.classicAddress);
    
    // Read escrow from XRPL
    const accountObjects = await client.request({
        command: 'account_objects',
        account: ESCROW_OWNER,
        type: 'escrow'
    });
    
    // Filter escrows where our user wallet is the destination
    const escrowsForUser = accountObjects.result.account_objects.filter(e => 
        e.Destination === userWallet.classicAddress
    );
    
    console.log(`🔍 Found ${escrowsForUser.length} escrows where our wallet (${userWallet.classicAddress}) is the destination`);
    
    console.log('All escrows found:', JSON.stringify(accountObjects.result.account_objects, null, 2));
    console.log('Escrows for our wallet:', JSON.stringify(escrowsForUser, null, 2));
    
    if (escrowsForUser.length === 0) {
        console.log('❌ No escrows found where our wallet is the destination');
        await client.disconnect();
        return;
    }
    
    const escrowsWithCondition = escrowsForUser.filter(e => e.Condition);
    // Find the most recent escrow (highest FinishAfter time) that matches our condition
    const currentTime = Math.floor(Date.now() / 1000);
    const ourConditionTarget = 'A0258020B7E060A60BB7A82F536A73C17BDE37A1B6CF5769EE4A8325BFF76C55A95B6AA4810120';
    
    // Convert UNIX time to Ripple Epoch for comparison
    const RIPPLE_EPOCH_DIFF = 946684800;
    const rippleCurrentTime = currentTime - RIPPLE_EPOCH_DIFF;
    
    console.log('⏰ Time conversion:');
    console.log('  UNIX current time:', currentTime);
    console.log('  Ripple current time:', rippleCurrentTime);
    
    const matchingEscrows = escrowsWithCondition.filter(e => 
        e.Condition === ourConditionTarget
        // Remove time filter - we'll select the newest one regardless
    );
    
    if (matchingEscrows.length === 0) {
        console.log('❌ No escrows with matching condition found');
        await client.disconnect();
        return;
    }
    
    console.log(`🔍 Found ${matchingEscrows.length} escrows with matching condition`);
    
    // Sort by PreviousTxnLgrSeq (ledger sequence) to get the NEWEST escrow
    matchingEscrows.sort((a, b) => b.PreviousTxnLgrSeq - a.PreviousTxnLgrSeq);
    const escrow = matchingEscrows[0];
    
    console.log(`📍 Selected escrow with FinishAfter: ${escrow.FinishAfter} (current: ${currentTime})`);
    
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
    // --- ADD THIS NEW BLOCK HERE ---
    const cancelAfter = escrow.CancelAfter;
    console.log('⏰ CancelAfter:', cancelAfter);
    if (cancelAfter) {
        console.log('⏰ Has escrow expired (based on CancelAfter)?', currentTime >= cancelAfter);
        if (currentTime >= cancelAfter) {
            console.log('❌ Escrow has expired and can no longer be finished. It can only be canceled by the owner.');
            await client.disconnect();
            return; // Exit the function if expired
        }
    }
    // --- END OF NEW BLOCK ---
    
    if (ourCondition.toLowerCase() === escrowCondition.toLowerCase()) {
        // ✅ SECRET IS CORRECT - proceed with crypto-condition escrow
        // Generate proper fulfillment using the correct XRPL approach:
        // The preimageCondition object IS the fulfillment, and serializeBinary() gives us the fulfillment hex
        const fulfillmentBinary = preimageCondition.serializeBinary();
        const fulfillment = fulfillmentBinary.toString('hex').toUpperCase();
        
        console.log('🔑 Fulfillment details:');
        console.log('  Fulfillment (hex):', fulfillment);
        console.log('  Fulfillment length:', fulfillment.length);
        
        // Additional timing check with larger buffer for XRPL ledger time
        const buffer = 60; // 60 second buffer for XRPL ledger time lag
        const finalTime = Math.floor(Date.now() / 1000);
        if (finalTime < finishAfter + buffer) {
            const waitTime = (finishAfter + buffer) - finalTime;
            console.log(`⏳ Need to wait ${waitTime} more seconds (including ${buffer}s buffer for XRPL ledger time)...`);
            await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
            console.log('✅ Wait complete!');
        }
        
        // Double-check timing after wait
        const newCurrentTime = Math.floor(Date.now() / 1000);
        console.log('🕐 Final timing check:');
        console.log('  Current time now:', newCurrentTime);
        console.log('  FinishAfter time:', finishAfter);
        console.log('  Ready to finish?:', newCurrentTime >= finishAfter);
        
        const escrowFinishTx = {
            TransactionType: 'EscrowFinish',
            Account: escrow.Destination, // ✅ Use the destination (who receives the funds)
            Owner: ESCROW_OWNER,
            OfferSequence: originalTx.result.Sequence, // Use sequence from original EscrowCreate
            Condition: escrow.Condition,
            Fulfillment: fulfillment
        };
        
            console.log('📋 EscrowFinish transaction details:');
    console.log(JSON.stringify(escrowFinishTx, null, 2));
    
    // Verify the destination account matches our wallet
    console.log('🔍 Account verification:');
    console.log('  Our wallet address:', userWallet.classicAddress);
    console.log('  Escrow destination:', escrow.Destination);
    console.log('  Accounts match?', userWallet.classicAddress === escrow.Destination);
    
    if (userWallet.classicAddress !== escrow.Destination) {
        console.log('❌ ERROR: Our wallet address does not match the escrow destination!');
        console.log('   We cannot finish this escrow because we are not the destination.');
        await client.disconnect();
        return;
    }
    
    console.log('🔍 DEBUGGING LINKS:');
    console.log('🔗 Check escrow on explorer:');
    console.log(`   https://testnet.xrpl.org/accounts/${ESCROW_OWNER}`);
    console.log('🔗 Original EscrowCreate transaction:');
    console.log(`   https://testnet.xrpl.org/transactions/${escrow.PreviousTxnID}`);
    
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