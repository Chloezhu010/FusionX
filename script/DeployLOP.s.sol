// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {LimitOrderProtocol} from "limit-order-protocol/contracts/LimitOrderProtocol.sol";
import {IWETH} from "solidity-utils/contracts/interfaces/IWETH.sol";
import {MockWETH} from "contracts/src/MockWETH.sol";

contract DeployLOP is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        vm.startBroadcast(deployerPrivateKey);
        
        // First deploy MockWETH
        MockWETH weth = new MockWETH();
        console.log("MockWETH deployed at:", address(weth));
        
        // Deploy the LimitOrderProtocol contract with WETH
        LimitOrderProtocol lop = new LimitOrderProtocol(IWETH(address(weth)));
        console.log("LimitOrderProtocol deployed at:", address(lop));
        
        vm.stopBroadcast();
        
        console.log("=== DEPLOYMENT SUMMARY ===");
        console.log("WETH:", address(weth));
        console.log("LimitOrderProtocol:", address(lop));
        console.log("=========================");
        console.log("Update your EscrowFactory to use LOP address:", address(lop));
    }
}