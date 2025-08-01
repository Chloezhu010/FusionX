// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {TestEscrowFactory} from "contracts/src/TestEscrowFactory.sol";
import {IBaseEscrow} from "contracts/lib/cross-chain-swap/contracts/interfaces/IBaseEscrow.sol";
import {IEscrowFactory} from "contracts/lib/cross-chain-swap/contracts/interfaces/IEscrowFactory.sol";
import {Address} from "solidity-utils/contracts/libraries/AddressLib.sol";
import {TimelocksLib} from "contracts/lib/cross-chain-swap/contracts/libraries/TimelocksLib.sol";

contract TriggerEvent is Script {
    function run() external {
        // --- CONFIGURATION ---
        address factoryAddress = vm.envAddress("ESCROW_FACTORY_ADDRESS");
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address maker = vm.addr(deployerPrivateKey);

        TestEscrowFactory factory = TestEscrowFactory(factoryAddress);

        // --- PREPARE DUMMY DATA ---
        // We will create some realistic-looking dummy data for the event.
        bytes32 orderHash = keccak256("my_test_order");
        bytes32 secret = keccak256("my_secret");
        bytes32 hashlock = keccak256(abi.encodePacked(secret));
        
        IBaseEscrow.Immutables memory immutables = IBaseEscrow.Immutables({
            orderHash: orderHash,
            hashlock: hashlock,
            maker: Address.wrap(maker),
            taker: Address.wrap(address(this)), // The script contract is the taker
            token: Address.wrap(0x7b79995e5f793A0722013363024a6C48ecf521F3), // WETH on Sepolia
            amount: 100 * 1e18, // 100 tokens
            safetyDeposit: 0.01 * 1e18,
            timelocks: TimelocksLib.Timelocks({
                deployedAt: uint40(block.timestamp),
                srcWithdrawal: uint40(block.timestamp + 60),
                srcPublicWithdrawal: uint40(block.timestamp + 120),
                srcCancellation: uint40(block.timestamp + 180),
                srcPublicCancellation: uint40(block.timestamp + 240),
                dstWithdrawal: uint40(block.timestamp + 60),
                dstPublicWithdrawal: uint40(block.timestamp + 120),
                dstCancellation: uint40(block.timestamp + 180)
            })
        });

        IEscrowFactory.DstImmutablesComplement memory immutablesComplement = IEscrowFactory.DstImmutablesComplement({
            maker: Address.wrap(maker),
            amount: 99 * 1e18, // 99 tokens
            token: Address.wrap(address(0)), // Represents native XRP
            safetyDeposit: 0.01 * 1e18,
            chainId: 42 // XRP Ledger chainId (example)
        });

        // --- TRIGGER EVENT ---
        vm.startBroadcast(deployerPrivateKey);

        factory.test_emitSrcEscrowCreated(immutables, immutablesComplement);

        vm.stopBroadcast();

        console.log("Successfully emitted SrcEscrowCreated event on factory:", address(factory));
    }
} 