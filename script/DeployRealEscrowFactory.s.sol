// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {IERC20} from "openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";
import {TestEscrowFactory} from "contracts/src/TestEscrowFactory.sol";

contract DeployRealEscrowFactory is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Use the deployed LOP and tokens
        address limitOrderProtocol = 0x72aB8EcE1ef0E10d5a396015E4996577860D97C5; // Our deployed LOP
        IERC20 usdc = IERC20(0x036CbD53842c5426634e7929541eC2318f3dCF7e); // Base Sepolia USDC
        
        // Deploy EscrowFactory with real LOP
        TestEscrowFactory factory = new TestEscrowFactory(
            limitOrderProtocol,  // Real 1inch LOP
            usdc,                // feeToken
            usdc,                // accessToken  
            deployer,            // owner
            86400,               // rescueDelaySrc (1 day)
            86400                // rescueDelayDst (1 day)
        );
        
        vm.stopBroadcast();
        
        console.log("=== PRODUCTION DEPLOYMENT ===");
        console.log("LimitOrderProtocol:", limitOrderProtocol);
        console.log("USDC Token:", address(usdc));
        console.log("EscrowFactory:", address(factory));
        console.log("=============================");
        console.log("Update your relayer to listen to:", address(factory));
        console.log("Now you can create REAL limit orders through the LOP!");
    }
}