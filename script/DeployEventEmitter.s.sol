// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {IBaseEscrow} from "contracts/lib/cross-chain-swap/contracts/interfaces/IBaseEscrow.sol";
import {IEscrowFactory} from "contracts/lib/cross-chain-swap/contracts/interfaces/IEscrowFactory.sol";
import {Address} from "solidity-utils/contracts/libraries/AddressLib.sol";
import {TimelocksLib, Timelocks} from "contracts/lib/cross-chain-swap/contracts/libraries/TimelocksLib.sol";

contract EventEmitter {
    event SrcEscrowCreated(IBaseEscrow.Immutables srcImmutables, IEscrowFactory.DstImmutablesComplement dstImmutablesComplement);
    
    function emitEvent(
        IBaseEscrow.Immutables memory immutables,
        IEscrowFactory.DstImmutablesComplement memory immutablesComplement
    ) external {
        emit SrcEscrowCreated(immutables, immutablesComplement);
    }
}

contract DeployEventEmitter is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy the EventEmitter contract - THIS CREATES A REAL CONTRACT
        EventEmitter emitter = new EventEmitter();
        
        vm.stopBroadcast();
        
        console.log("EventEmitter deployed at:", address(emitter));
        console.log("Update your relayer to listen to this address!");
    }
}