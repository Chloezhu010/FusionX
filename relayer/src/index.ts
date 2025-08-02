import { ethers } from 'ethers';
import { Client, Wallet, xrpToDrops, EscrowCreate } from 'xrpl';
import { config } from './config';
const cc = require('five-bells-condition');

const escrowFactoryAbi = [
    "event SrcEscrowCreated((bytes32,bytes32,uint256,uint256,uint256,uint256,uint256,uint256) srcImmutables, (uint256,uint256,uint256,uint256,uint256) dstImmutablesComplement)"
];

async function main() {
    console.log('Starting relayer...');

    const provider = new ethers.WebSocketProvider(config.ethereum.nodeWsUrl);
    
    const escrowFactory = new ethers.Contract(config.ethereum.escrowFactoryAddress, escrowFactoryAbi, provider);

    console.log(`Listening for SrcEscrowCreated events on ${config.ethereum.escrowFactoryAddress}`);
    
    // Debug: Check the event topic hash
    const iface = new ethers.Interface(escrowFactoryAbi);
    const eventTopic = iface.getEvent('SrcEscrowCreated')?.topicHash;
    console.log('Expected event topic:', eventTopic);
    console.log('Actual event topic from tx: 0x0e534c62f0afd2fa0f0fa71198e8aa2d549f24daf2bb47de0d5486c7ce9288ca');
    
    // Test WebSocket by listening to new blocks (this will show if connection works)
    provider.on('block', (blockNumber) => {
        console.log(`📦 New block: ${blockNumber}`);
    });

    escrowFactory.on('SrcEscrowCreated', (srcImmutables, dstImmutablesComplement, event) => {
        console.log('--- New SrcEscrowCreated Event ---');
        console.log('🎉 EVENT DETECTED! 🎉');
        console.log('Source Immutables:', srcImmutables);
        console.log('Dest Immutables Complement:', dstImmutablesComplement);
        console.log('Transaction Hash:', event.log.transactionHash);
        console.log('Order Hash:', srcImmutables[0]);
        console.log('Hashlock:', srcImmutables[1]);
        console.log('---------------------------------');

        handleXrplEscrowCreation(srcImmutables, dstImmutablesComplement);
    });
    
    // Add a simple test to verify the contract setup
    console.log('🔍 Contract setup complete, waiting for events...');
    
    // Also start monitoring XRPL for EscrowFinish transactions
    monitorXrplEscrowFinish().catch((error) => {
        console.error('XRPL monitoring error:', error);
    });
}

async function handleXrplEscrowCreation(srcImmutables: any, dstImmutablesComplement: any) {
    console.log('--- Preparing XRPL Escrow ---');

    // Extract data from the arrays
    const orderHash = srcImmutables[0];
    const hashlock = srcImmutables[1];
    // Extract XRP amount from dstImmutablesComplement (in drops, convert to XRP)
    const xrpDrops = Number(dstImmutablesComplement[1]);
    const xrpAmount = (xrpDrops / 1000000).toString(); // Convert drops to XRP

    console.log('📋 Cross-chain swap details:');
    console.log('Order Hash:', orderHash);
    console.log('Hashlock:', hashlock);
    console.log('XRP Amount:', xrpAmount);

    const xrplClient = new Client(config.xrpl.nodeUrl);
    await xrplClient.connect();

    const relayerWallet = Wallet.fromSeed(config.xrpl.relayerWalletSeed);

    // For demo purposes, make escrow finishable immediately (add 15 seconds)
    const finishAfter = Math.floor(Date.now() / 1000) + 15; // 15 seconds from now


    // Create proper crypto-condition using five-bells-condition library
    // We need to use the secret (orderHash) to generate a proper preimage condition
    const secret = orderHash; // The orderHash IS the secret used for the condition
    const secretBuffer = Buffer.from(secret.slice(2), 'hex');
    
    // Create preimage condition using correct API
    const preimageCondition = new cc.PreimageSha256();
    preimageCondition.setPreimage(secretBuffer);
    
    // Generate the condition binary and encode to hex (XRPL expects hex, not base64)
    const conditionBinary = preimageCondition.getConditionBinary();
    const condition = conditionBinary.toString('hex').toUpperCase();
    
    console.log('🔐 Crypto-condition details:');
    console.log('  Secret (hex):', secret);
    console.log('  Hashlock (hex):', hashlock);
    console.log('  Condition (hex):', condition);
    console.log('  Condition length:', condition.length, 'chars');

    const escrowCreateTx: EscrowCreate = {
        TransactionType: 'EscrowCreate',
        Account: relayerWallet.classicAddress,
        Amount: xrpToDrops(xrpAmount),
        Destination: config.xrpl.destinationAddress,
        Condition: condition,
        FinishAfter: finishAfter,
        Memos: [
            {
                Memo: {
                    MemoType: Buffer.from('eth_tx_hash').toString('hex').toUpperCase(),
                    MemoData: orderHash.slice(2).toUpperCase()
                }
            },
            {
                Memo: {
                    MemoType: Buffer.from('hashlock').toString('hex').toUpperCase(),
                    MemoData: hashlock.slice(2).toUpperCase()
                }
            }
        ]
    };

    console.log('Prepared XRPL EscrowCreate Transaction:');
    console.log(escrowCreateTx);

    try {
        const prepared = await xrplClient.autofill(escrowCreateTx);
        const signed = relayerWallet.sign(prepared);
        console.log(`Submitting XRPL transaction: ${signed.tx_blob}`);
        
        console.log('📡 Submitting XRPL transaction (fire-and-forget)...');
        
        // Use submit instead of submitAndWait to avoid hanging on testnet
        const result = await xrplClient.submit(signed.tx_blob);
        console.log('✅ XRPL Transaction submitted:', result);
        
        if (result.result.engine_result === 'tesSUCCESS') {
            console.log('🎉 XRPL Escrow transaction accepted by network!');
            console.log('💡 Transaction hash:', result.result.tx_json.hash);
            console.log('🔗 Check status at: https://testnet.xrpl.org/transactions/' + result.result.tx_json.hash);
        } else if (result.result.engine_result === 'terQUEUED') {
            console.log('⏳ Transaction queued, will be processed when network is ready');
        } else {
            console.log('❌ Transaction failed:', result.result.engine_result);
            console.log('📝 Error message:', result.result.engine_result_message);
        }
    } catch (error) {
        console.error("❌ Error submitting XRPL transaction:", error);
        console.error("Error details:", JSON.stringify(error, null, 2));
    }


    await xrplClient.disconnect();
    console.log('-----------------------------');
}

// NEW: Monitor XRPL for EscrowFinish transactions to extract revealed secrets
async function monitorXrplEscrowFinish() {
    console.log('🔍 Starting XRPL EscrowFinish monitor...');
    
    const xrplClient = new Client(config.xrpl.nodeUrl);
    await xrplClient.connect();
    
    // Subscribe to all transactions to catch EscrowFinish
    await xrplClient.request({
        command: 'subscribe',
        streams: ['transactions']
    });
    
    xrplClient.on('transaction', (data: any) => {
        const tx = data?.transaction;
        
        // Check if this is an EscrowFinish transaction involving our relayer
        if (tx && tx.TransactionType === 'EscrowFinish' && 
            tx.Owner === 'rfNXwvo8vyPRD7Sd1ZYkF9wVc19uwzMWnW') { // Our relayer address
            
            console.log('🔑 EscrowFinish detected! Secret revealed!');
            console.log('Transaction:', tx);
            
            if (tx.Fulfillment) {
                const revealedSecret = '0x' + tx.Fulfillment.toLowerCase();
                console.log('✨ Revealed Secret:', revealedSecret);
                
                // TODO: Now use this secret to claim USDC on EVM side
                handleSecretRevealed(revealedSecret, tx);
            }
        }
    });
    
    console.log('👀 Monitoring XRPL for EscrowFinish transactions...');
}

async function handleSecretRevealed(secret: string, escrowFinishTx: any) {
    console.log('🎯 Processing revealed secret for EVM withdrawal...');
    console.log('Secret:', secret);
    console.log('XRPL Tx Hash:', escrowFinishTx.hash);
    
    // TODO: Implement EVM escrow withdrawal using the revealed secret
    // This would call the withdraw function on the EscrowSrc contract
    console.log('📝 TODO: Implement EVM escrow withdrawal');
    console.log('- Find corresponding EVM escrow by hashlock');
    console.log('- Call withdraw() function with revealed secret');
    console.log('- Claim USDC on Base Sepolia');
}

main().catch((error) => {
    console.error('Error:', error);
    process.exit(1);
});
