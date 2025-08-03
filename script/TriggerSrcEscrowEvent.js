const { ethers } = require('ethers');
require('dotenv').config({ path: '../relayer/.env' });

async function triggerSrcEscrowEvent() {
    console.log('🚀 Triggering SrcEscrowCreated event for relayer testing...');
    
    // Configuration
    const provider = new ethers.JsonRpcProvider('https://sepolia.base.org');
    const privateKey = process.env.PRIVATE_KEY;
    const wallet = new ethers.Wallet(privateKey, provider);
    
    const ESCROW_FACTORY_ADDRESS = '0x3DB3905Bb80ed675c7cAb292Ad1Bc52Cd8058647';
    const EXISTING_ESCROW = '0x6767eC16FD015735CD0416F7686Ab086d287A44A'; // The escrow we already funded
    const SECRET = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef';
    
    console.log('📋 Configuration:');
    console.log('  Factory address:', ESCROW_FACTORY_ADDRESS);
    console.log('  Existing funded escrow:', EXISTING_ESCROW);
    console.log('  Secret:', SECRET);
    
    // Create the parameters that match our existing escrow
    const hashlock = ethers.keccak256(SECRET);
    const orderHash = ethers.keccak256(ethers.toUtf8Bytes(`trigger_event_${Date.now()}`));
    
    const currentTime = Math.floor(Date.now() / 1000);
    const timelocks = BigInt(currentTime) << 224n;
    
    const srcImmutables = {
        orderHash: orderHash,
        hashlock: hashlock,
        maker: wallet.address,
        taker: wallet.address,
        token: '0x036CbD53842c5426634e7929541eC2318f3dCF7e', // USDC
        amount: 5_000_000, // 5 USDC
        safetyDeposit: ethers.parseEther('0.001'),
        timelocks: timelocks
    };
    
    const dstImmutablesComplement = {
        maker: wallet.address,
        amount: 1_800_000, // 1.8 XRP in drops
        token: 0, // Native XRP
        safetyDeposit: ethers.parseEther('0.001'),
        chainId: 1440002 // XRPL testnet
    };
    
    console.log('📊 Event parameters:');
    console.log('  Order Hash:', orderHash);
    console.log('  Hashlock:', hashlock);
    console.log('  USDC Amount:', '5.0 USDC');
    console.log('  XRP Amount:', '1.8 XRP');
    
    try {
        // We'll use the event emitter contract we used before, but emit a SrcEscrowCreated event
        const eventEmitterAbi = [
            "function emitEvent((bytes32,bytes32,uint256,uint256,uint256,uint256,uint256,uint256) srcImmutables, (uint256,uint256,uint256,uint256,uint256) dstImmutablesComplement)"
        ];
        
        const eventEmitter = new ethers.Contract('0x1C4d0595017E9840a3E79Ab5BA629836C4f8Bd92', eventEmitterAbi, wallet);
        
        console.log('📡 Emitting SrcEscrowCreated event...');
        const tx = await eventEmitter.emitEvent(
            Object.values(srcImmutables),
            Object.values(dstImmutablesComplement)
        );
        
        console.log('⏳ Transaction submitted:', tx.hash);
        const receipt = await tx.wait();
        
        console.log('🎉 SUCCESS! SrcEscrowCreated event emitted!');
        console.log('  Block number:', receipt.blockNumber);
        console.log('  Gas used:', receipt.gasUsed.toString());
        console.log('');
        console.log('👀 Your relayer should now detect this event and:');
        console.log('  1. See the SrcEscrowCreated event');
        console.log('  2. Create corresponding XRPL escrow with same hashlock');
        console.log('  3. Wait for you to finish the XRPL escrow to reveal the secret');
        console.log('');
        console.log('📝 Key info for relayer:');
        console.log('  Event tx:', tx.hash);
        console.log('  Hashlock:', hashlock);
        console.log('  Secret (for testing):', SECRET);
        console.log('  Funded escrow with USDC:', EXISTING_ESCROW);
        console.log('');
        console.log('🔗 View on explorer:');
        console.log(`  https://sepolia.basescan.org/tx/${tx.hash}`);
        
        return {
            success: true,
            txHash: tx.hash,
            hashlock,
            secret: SECRET,
            fundedEscrow: EXISTING_ESCROW
        };
        
    } catch (error) {
        console.error('❌ Error emitting event:', error.message);
        return { success: false, error: error.message };
    }
}

triggerSrcEscrowEvent().catch(console.error);