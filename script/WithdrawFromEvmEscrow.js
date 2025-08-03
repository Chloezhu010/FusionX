const { ethers } = require('ethers');
require('dotenv').config({ path: '../relayer/.env' });

async function withdrawFromEvmEscrow() {
    console.log('🎯 Starting EVM escrow withdrawal...');
    console.log('Goal: Resolver uses revealed secret to claim 5 USDC as payment for cross-chain service');
    
    // Configuration
    const provider = new ethers.JsonRpcProvider('https://sepolia.base.org');
    
    // Resolver configuration - the resolver withdraws as payment for the service
    const RESOLVER_ADDRESS = '0x45BcD0c355de22d57F7911CdaD43E471f8BDBa1d';
    
    // For demo, we'll use your private key to simulate the resolver
    // In production, the resolver would have its own private key
    const privateKey = process.env.PRIVATE_KEY;
    const wallet = new ethers.Wallet(privateKey, provider);
    
    // The real funded escrow we created
    const REAL_ESCROW_ADDRESS = '0x6767eC16FD015735CD0416F7686Ab086d287A44A'; // Has 5 USDC + 0.001 ETH
    const SECRET = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef';
    const HASHLOCK = '0xcae36a6a44328f3fb063df12b0cf3fa225a3c6dbdd6acef0f6e619d33890cf24';
    const USDC_ADDRESS = '0x036CbD53842c5426634e7929541eC2318f3dCF7e';
    
    console.log('📋 Configuration:');
    console.log('  Transaction sender:', wallet.address, '(using your key for demo)');
    console.log('  Resolver address:', RESOLVER_ADDRESS, '(receives USDC)');
    console.log('  Escrow address:', REAL_ESCROW_ADDRESS);
    console.log('  Secret:', SECRET);
    console.log('  Hashlock:', HASHLOCK);
    
    // Verify secret matches hashlock
    const computedHashlock = ethers.keccak256(SECRET);
    console.log('🔐 Secret verification:');
    console.log('  Computed hashlock:', computedHashlock);
    console.log('  Expected hashlock:', HASHLOCK);
    console.log('  Secrets match:', computedHashlock.toLowerCase() === HASHLOCK.toLowerCase() ? '✅' : '❌');
    
    if (computedHashlock.toLowerCase() !== HASHLOCK.toLowerCase()) {
        console.log('❌ Secret does not match hashlock - cannot withdraw');
        return;
    }
    
    // Check escrow current state
    console.log('🔍 Checking escrow state...');
    const usdcAbi = ["function balanceOf(address) view returns (uint256)"];
    const usdcContract = new ethers.Contract(USDC_ADDRESS, usdcAbi, provider);
    
    const escrowUsdcBalance = await usdcContract.balanceOf(REAL_ESCROW_ADDRESS);
    const escrowEthBalance = await provider.getBalance(REAL_ESCROW_ADDRESS);
    
    console.log('  Escrow USDC balance:', Number(escrowUsdcBalance) / 1e6, 'USDC');
    console.log('  Escrow ETH balance:', ethers.formatEther(escrowEthBalance), 'ETH');
    
    if (Number(escrowUsdcBalance) === 0) {
        console.log('❌ Escrow has no USDC to withdraw');
        return;
    }
    
    // Check resolver balances before withdrawal
    console.log('💳 Resolver balances before withdrawal:');
    const resolverUsdcBefore = await usdcContract.balanceOf(RESOLVER_ADDRESS);
    console.log('  Resolver USDC balance:', Number(resolverUsdcBefore) / 1e6, 'USDC');
    
    console.log('💳 Transaction sender balances:');
    const senderUsdcBefore = await usdcContract.balanceOf(wallet.address);
    const senderEthBefore = await provider.getBalance(wallet.address);
    console.log('  Sender USDC balance:', Number(senderUsdcBefore) / 1e6, 'USDC');
    console.log('  Sender ETH balance:', ethers.formatEther(senderEthBefore), 'ETH');
    
    try {
        // Reconstruct the immutables for the withdraw call
        const orderHash = ethers.keccak256(ethers.toUtf8Bytes('manual_order_test'));
        const currentTime = Math.floor(Date.now() / 1000);
        const timelocks = BigInt(currentTime) << 224n;
        
        const immutables = {
            orderHash: orderHash,
            hashlock: HASHLOCK,
            maker: wallet.address,
            taker: wallet.address,
            token: USDC_ADDRESS,
            amount: 5_000_000, // 5 USDC
            safetyDeposit: ethers.parseEther('0.001'),
            timelocks: timelocks
        };
        
        console.log('📊 Withdrawal parameters:');
        console.log('  Order Hash:', immutables.orderHash);
        console.log('  Token:', immutables.token);
        console.log('  Amount:', Number(immutables.amount) / 1e6, 'USDC');
        console.log('  Safety Deposit:', ethers.formatEther(immutables.safetyDeposit), 'ETH');
        
        // Call basic withdraw function - USDC goes to msg.sender (transaction sender)
        const escrowAbi = [
            "function withdraw(bytes32 secret, (bytes32,bytes32,uint256,uint256,uint256,uint256,uint256,uint256) immutables)"
        ];
        
        const escrowContract = new ethers.Contract(REAL_ESCROW_ADDRESS, escrowAbi, wallet);
        
        console.log('💰 Attempting withdrawal...');
        console.log('  USDC will be sent to transaction sender:', wallet.address);
        console.log('  (In real system, resolver would use their own private key)');
        
        // Use basic withdraw - tokens go to msg.sender
        const withdrawTx = await escrowContract.withdraw(SECRET, Object.values(immutables));
        
        console.log('⏳ Transaction submitted:', withdrawTx.hash);
        const receipt = await withdrawTx.wait();
        
        console.log('🎉 SUCCESS! Withdrawal completed!');
        console.log('  Block number:', receipt.blockNumber);
        console.log('  Gas used:', receipt.gasUsed.toString());
        
        // Check balances after withdrawal
        console.log('💳 Transaction sender balances after withdrawal:');
        const senderUsdcAfter = await usdcContract.balanceOf(wallet.address);
        const senderEthAfter = await provider.getBalance(wallet.address);
        console.log('  Sender USDC balance:', Number(senderUsdcAfter) / 1e6, 'USDC');
        console.log('  Sender ETH balance:', ethers.formatEther(senderEthAfter), 'ETH');
        
        const usdcGained = Number(senderUsdcAfter - senderUsdcBefore) / 1e6;
        console.log('  USDC gained by sender:', usdcGained, 'USDC');
        
        console.log('💳 Resolver balances after withdrawal:');
        const resolverUsdcAfter = await usdcContract.balanceOf(RESOLVER_ADDRESS);
        console.log('  Resolver USDC balance:', Number(resolverUsdcAfter) / 1e6, 'USDC');
        
        console.log('🔗 View on explorer:');
        console.log(`  https://sepolia.basescan.org/tx/${withdrawTx.hash}`);
        console.log(`  https://sepolia.basescan.org/address/${REAL_ESCROW_ADDRESS}`);
        
        console.log('');
        console.log('🎯 CROSS-CHAIN ATOMIC SWAP COMPLETED!');
        console.log('  ✅ Base Sepolia escrow created with 5 USDC locked');
        console.log('  ✅ XRPL escrow created by relayer');
        console.log('  ✅ XRPL escrow finished (secret revealed)');
        console.log('  ✅ Secret used to withdraw USDC from Base Sepolia');
        
        return {
            success: true,
            txHash: withdrawTx.hash,
            usdcWithdrawn: usdcGained
        };
        
    } catch (error) {
        console.error('❌ Error during withdrawal:', error.message);
        
        if (error.message.includes('Invalid secret')) {
            console.log('💡 The secret provided does not match the escrow hashlock');
        } else if (error.message.includes('Too early')) {
            console.log('💡 The withdrawal period has not started yet');
        } else if (error.message.includes('call revert exception')) {
            console.log('💡 This escrow may not have the withdraw function or wrong parameters');
        }
        
        return { success: false, error: error.message };
    }
}

withdrawFromEvmEscrow().catch(console.error);