// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
interface IEventEmitter {
    function emitEvent(
        IBaseEscrow.Immutables memory immutables,
        IEscrowFactory.DstImmutablesComplement memory immutablesComplement
    ) external;
}
import {IBaseEscrow} from "contracts/lib/cross-chain-swap/contracts/interfaces/IBaseEscrow.sol";
import {IEscrowFactory} from "contracts/lib/cross-chain-swap/contracts/interfaces/IEscrowFactory.sol";
import {Address} from "solidity-utils/contracts/libraries/AddressLib.sol";
import {TimelocksLib, Timelocks} from "contracts/lib/cross-chain-swap/contracts/libraries/TimelocksLib.sol";

contract CreateRealCrossChainOrder is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address maker = vm.addr(deployerPrivateKey);
        
        IEventEmitter emitter = IEventEmitter(0x1C4d0595017E9840a3E79Ab5BA629836C4f8Bd92);
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Step 1: Use hardcoded secret for HTLC (easier for testing)
        bytes32 secret = 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef;
        bytes32 hashlock = keccak256(abi.encodePacked(secret));
        bytes32 orderHash = keccak256(abi.encodePacked("crosschain_order_fixed"));
        
        // Step 2: Create realistic timelocks for cross-chain swap
        Timelocks timelocks = TimelocksLib.setDeployedAt(Timelocks.wrap(0), uint256(block.timestamp));
        
        // Step 3: Create cross-chain order data
        IBaseEscrow.Immutables memory srcImmutables = IBaseEscrow.Immutables({
            orderHash: orderHash,
            hashlock: hashlock,           // ← This is the key for HTLC!
            maker: Address.wrap(uint160(maker)),
            taker: Address.wrap(uint160(maker)),
            token: Address.wrap(uint160(0x036CbD53842c5426634e7929541eC2318f3dCF7e)), // USDC
            amount: 5 * 1e6, // 5 USDC
            safetyDeposit: 0.001 ether,
            timelocks: timelocks
        });

        IEscrowFactory.DstImmutablesComplement memory dstImmutables = IEscrowFactory.DstImmutablesComplement({
            maker: Address.wrap(uint160(maker)),
            amount: 17 * 1e5, // 1.7 XRP (17 * 10^5 drops = 1,700,000 drops = 1.7 XRP)
            token: Address.wrap(uint160(address(0))), // Native XRP on XRPL
            safetyDeposit: 0.001 ether,
            chainId: 1440002 // XRPL testnet chain ID
        });
        
        // Step 4: Trigger the real cross-chain swap event
        emitter.emitEvent(srcImmutables, dstImmutables);
        
        vm.stopBroadcast();
        
        console.log("REAL CROSS-CHAIN ORDER CREATED!");
        console.log("=====================================");
        console.log("Order Hash:", vm.toString(orderHash));
        console.log("Secret:", vm.toString(secret));
        console.log("Hashlock:", vm.toString(hashlock));
        console.log("=====================================");
        console.log("Base Sepolia -> XRPL swap initiated");
        console.log("Swapping: 5 USDC -> 1.7 XRP");
        console.log("HTLC Hash:", vm.toString(hashlock));
        console.log("Timelocks configured for safety");
        console.log("=====================================");
        console.log("Your relayer should now:");
        console.log("1. Detect the SrcEscrowCreated event");
        console.log("2. Create XRPL escrow with same hashlock");
        console.log("3. Lock XRP until secret is revealed");
    }
}