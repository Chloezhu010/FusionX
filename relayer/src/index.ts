import { ethers } from 'ethers';
import { Client, Wallet, xrpToDrops, EscrowCreate } from 'xrpl';
import { config } from './config';

const escrowFactoryAbi = [
    "event SrcEscrowCreated(tuple(bytes32 orderHash, bytes32 hashlock, address maker, address taker, address token, uint256 amount, uint128 safetyDeposit, tuple(uint40 deployedAt, uint40 srcWithdrawal, uint40 srcPublicWithdrawal, uint40 srcCancellation, uint40 srcPublicCancellation, uint40 dstWithdrawal, uint40 dstPublicWithdrawal, uint40 dstCancellation) timelocks) immutables, tuple(address maker, uint256 amount, address token, uint128 safetyDeposit, uint256 chainId) immutablesComplement)"
];

async function main() {
    console.log('Starting relayer...');

    const provider = new ethers.WebSocketProvider(config.ethereum.nodeWsUrl);
    const escrowFactory = new ethers.Contract(config.ethereum.escrowFactoryAddress, escrowFactoryAbi, provider);

    console.log(`Listening for SrcEscrowCreated events on ${config.ethereum.escrowFactoryAddress}`);

    escrowFactory.on('SrcEscrowCreated', (immutables, immutablesComplement, event) => {
        console.log('--- New SrcEscrowCreated Event ---');
        console.log('Immutables:', immutables);
        console.log('Immutables Complement:', immutablesComplement);
        console.log('Transaction Hash:', event.log.transactionHash);
        console.log('---------------------------------');

        handleXrplEscrowCreation(immutables, immutablesComplement);
    });
}

async function handleXrplEscrowCreation(immutables: any, immutablesComplement: any) {
    console.log('--- Preparing XRPL Escrow ---');

    // In a real implementation, you would need a mechanism to determine the XRP amount.
    // This could be from the order, a price oracle, or a fixed rate.
    // For now, we'll use a placeholder value.
    const xrpAmount = "100"; // 100 XRP

    const xrplClient = new Client(config.xrpl.nodeUrl);
    await xrplClient.connect();

    const relayerWallet = Wallet.fromSeed(config.xrpl.relayerWalletSeed);

    // The Ripple Epoch is 946684800 seconds after the Unix Epoch.
    const RIPPLE_EPOCH_OFFSET = 946684800;
    const finishAfter = Number(immutables.timelocks.dstCancellation) - RIPPLE_EPOCH_OFFSET;


    const escrowCreateTx: EscrowCreate = {
        TransactionType: 'EscrowCreate',
        Account: relayerWallet.classicAddress,
        Amount: xrpToDrops(xrpAmount),
        Destination: config.xrpl.destinationAddress,
        // Condition must be a 64-character uppercase hex string
        Condition: immutables.hashlock.slice(2).toUpperCase(),
        FinishAfter: finishAfter,
        Memos: [
            {
                Memo: {
                    MemoType: ethers.hexlify(ethers.toUtf8Bytes('eth_tx_hash')),
                    MemoData: ethers.hexlify(ethers.toUtf8Bytes(immutables.orderHash))
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
