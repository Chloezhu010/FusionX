// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {TestEscrowFactory} from "contracts/src/TestEscrowFactory.sol";
import {IERC20} from "openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";
import {Address} from "solidity-utils/contracts/libraries/AddressLib.sol";

contract DeployFactory is Script {
    function run() external returns (TestEscrowFactory) {
        // --- CONFIGURATION ---
        
        // You MUST replace these with the correct addresses for the Sepolia testnet.
        // Find them on a block explorer like Sepolia Etherscan.
        address limitOrderProtocol = 0xE53136D9De56672e8D2665C98653AC7b8A60Dc44; // 1inch LOP on Sepolia Base
        IERC20 feeToken = IERC20(address(1));     // Using address(0) to disable fees
        IERC20 accessToken = IERC20(address(1));
        uint32 rescueDelay = 60; // 1 minute

        // Get the private key from the environment variable
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address owner = vm.addr(deployerPrivateKey);

        // --- DEPLOYMENT ---

        vm.startBroadcast(deployerPrivateKey);

        TestEscrowFactory factory = new TestEscrowFactory(
            limitOrderProtocol,
            feeToken,
            accessToken,
            owner,
            rescueDelay,
            rescueDelay
        );

        vm.stopBroadcast();

        console.log("TestEscrowFactory deployed at:", address(factory));
        return factory;
    }
} 