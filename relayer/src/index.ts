import { ethers } from 'ethers';
import { Client, Wallet, xrpToDrops, EscrowCreate } from 'xrpl';
import { config } from './config';

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

    // For now, use a simple timeout (in production, extract from timelocks)
    const finishAfter = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now


    const escrowCreateTx: EscrowCreate = {
        TransactionType: 'EscrowCreate',
        Account: relayerWallet.classicAddress,
        Amount: xrpToDrops(xrpAmount),
        Destination: config.xrpl.destinationAddress,
        // Condition must be a 64-character uppercase hex string
        Condition: hashlock.slice(2).toUpperCase(),
        FinishAfter: finishAfter,
        Memos: [
            {
                Memo: {
                    MemoType: Buffer.from('eth_tx_hash').toString('hex').toUpperCase(),
                    MemoData: orderHash.slice(2).toUpperCase()
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
        const result = await xrplClient.submitAndWait(signed.tx_blob);
        console.log('XRPL Transaction Result:', result);
    } catch (error) {
        console.error("Error submitting XRPL transaction:", error);
    }


    await xrplClient.disconnect();
    console.log('-----------------------------');
}

main().catch((error) => {
    console.error('Error:', error);
    process.exit(1);
});
