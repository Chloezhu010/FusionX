// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {IBaseEscrow} from "contracts/lib/cross-chain-swap/contracts/interfaces/IBaseEscrow.sol";
import {IEscrowFactory} from "contracts/lib/cross-chain-swap/contracts/interfaces/IEscrowFactory.sol";
import {Address} from "solidity-utils/contracts/libraries/AddressLib.sol";
import {TimelocksLib, Timelocks} from "contracts/lib/cross-chain-swap/contracts/libraries/TimelocksLib.sol";

contract TriggerEvent is Script {
    // Declare the event in this contract so we can emit it directly
    event SrcEscrowCreated(IBaseEscrow.Immutables srcImmutables, IEscrowFactory.DstImmutablesComplement dstImmutablesComplement);

    function run() external {
        // --- CONFIGURATION ---
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address maker = vm.addr(deployerPrivateKey);

        // --- PREPARE DUMMY DATA ---
        // We will create some realistic-looking dummy data for the event.
        bytes32 orderHash = keccak256("my_test_order");
        bytes32 secret = keccak256("my_secret");
        bytes32 hashlock = keccak256(abi.encodePacked(secret));
        
        // Create timelocks using the correct type
        Timelocks timelocks = TimelocksLib.setDeployedAt(Timelocks.wrap(0), uint256(block.timestamp));
        
        IBaseEscrow.Immutables memory immutables = IBaseEscrow.Immutables({
            orderHash: orderHash,
            hashlock: hashlock,
            maker: Address.wrap(uint160(maker)),
            taker: Address.wrap(uint160(maker)), // Use maker as taker for testing
            token: Address.wrap(uint160(0x7b79995E5f793a0722013363024A6c48ECF521F3)), // WETH on Sepolia (corrected checksum)
            amount: 100 * 1e18, // 100 tokens
            safetyDeposit: 0.01 * 1e18,
            timelocks: timelocks
        });

        IEscrowFactory.DstImmutablesComplement memory immutablesComplement = IEscrowFactory.DstImmutablesComplement({
            maker: Address.wrap(uint160(maker)),
            amount: 99 * 1e18, // 99 tokens
            token: Address.wrap(uint160(address(0))), // Represents native XRP
            safetyDeposit: 0.01 * 1e18,
            chainId: 42 // XRP Ledger chainId (example)
        });

        // --- TRIGGER EVENT ---
        vm.startBroadcast(deployerPrivateKey);
        
        // Emit the event directly from this contract
        emit SrcEscrowCreated(immutables, immutablesComplement);

        vm.stopBroadcast();

        console.log("Successfully emitted SrcEscrowCreated event!");
        console.log("OrderHash:", vm.toString(orderHash));
        console.log("Hashlock:", vm.toString(hashlock));
    }
} 