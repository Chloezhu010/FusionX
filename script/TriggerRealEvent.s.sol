// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {IBaseEscrow} from "contracts/lib/cross-chain-swap/contracts/interfaces/IBaseEscrow.sol";
import {IEscrowFactory} from "contracts/lib/cross-chain-swap/contracts/interfaces/IEscrowFactory.sol";
import {Address} from "solidity-utils/contracts/libraries/AddressLib.sol";
import {TimelocksLib, Timelocks} from "contracts/lib/cross-chain-swap/contracts/libraries/TimelocksLib.sol";

interface IEventEmitter {
    function emitEvent(
        IBaseEscrow.Immutables memory immutables,
        IEscrowFactory.DstImmutablesComplement memory immutablesComplement
    ) external;
}

contract TriggerRealEvent is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address maker = vm.addr(deployerPrivateKey);
        
        // Address of the deployed EventEmitter contract
        address eventEmitterAddress = 0x071e3Ae87D4aA62d0D7977C47248B0f9B185B96f;
        IEventEmitter emitter = IEventEmitter(eventEmitterAddress);

        // Prepare event data
        bytes32 orderHash = keccak256("my_test_order");
        bytes32 secret = keccak256("my_secret");
        bytes32 hashlock = keccak256(abi.encodePacked(secret));
        
        Timelocks timelocks = TimelocksLib.setDeployedAt(Timelocks.wrap(0), uint256(block.timestamp));
        
        IBaseEscrow.Immutables memory immutables = IBaseEscrow.Immutables({
            orderHash: orderHash,
            hashlock: hashlock,
            maker: Address.wrap(uint160(maker)),
            taker: Address.wrap(uint160(maker)),
            token: Address.wrap(uint160(0x036CbD53842c5426634e7929541eC2318f3dCF7e)), // USDC on Base Sepolia
            amount: 100 * 1e6, // 100 USDC (6 decimals)
            safetyDeposit: 0.001 ether,
            timelocks: timelocks
        });

        IEscrowFactory.DstImmutablesComplement memory immutablesComplement = IEscrowFactory.DstImmutablesComplement({
            maker: Address.wrap(uint160(maker)),
            amount: 99 * 1e6, // 99 USDC
            token: Address.wrap(uint160(address(0))), // Native XRP
            safetyDeposit: 0.001 ether,
            chainId: 1440002 // XRP Ledger testnet chainId
        });

        vm.startBroadcast(deployerPrivateKey);
        
        // Call the deployed contract to emit the event - THIS IS A REAL TRANSACTION
        emitter.emitEvent(immutables, immutablesComplement);
        
        vm.stopBroadcast();

        console.log("Real SrcEscrowCreated event emitted from contract:", eventEmitterAddress);
        console.log("OrderHash:", vm.toString(orderHash));
        console.log("Hashlock:", vm.toString(hashlock));
    }
}