const { ethers } = require('ethers');

async function checkContract() {
    console.log('🔍 Checking Factory Contract on Base Sepolia...');
    
    const provider = new ethers.JsonRpcProvider('https://sepolia.base.org');
    const factoryAddress = '0x071e3Ae87D4aA62d0D7977C47248B0f9B185B96f';
    
    try {
        // Check if contract exists
        const code = await provider.getCode(factoryAddress);
        console.log('Contract code length:', code.length);
        
        if (code === '0x') {
            console.log('❌ No contract found at address:', factoryAddress);
            return;
        }
        
        console.log('✅ Contract exists at address:', factoryAddress);
        
        // Try to get the contract's owner
        const factory = new ethers.Contract(factoryAddress, [
            'function owner() view returns (address)',
            'function test_emitSrcEscrowCreated(tuple(bytes32,bytes32,address,address,address,uint256,uint256,uint256), tuple(address,uint256,address,uint128,uint256)) external'
        ], provider);
        
        try {
            const owner = await factory.owner();
            console.log('✅ Factory owner:', owner);
        } catch (error) {
            console.log('❌ Could not get owner:', error.message);
        }
        
        // Check if the test function exists
        try {
            const hasTestFunction = await factory.test_emitSrcEscrowCreated.staticCall;
            console.log('✅ test_emitSrcEscrowCreated function exists');
        } catch (error) {
            console.log('❌ test_emitSrcEscrowCreated function not found:', error.message);
        }
        
    } catch (error) {
        console.error('❌ Error checking contract:', error.message);
    }
}

checkContract(); 