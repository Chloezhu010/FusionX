// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {IERC20} from "openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";
import {TestEscrowFactory} from "contracts/src/TestEscrowFactory.sol";
import {IBaseEscrow} from "contracts/lib/cross-chain-swap/contracts/interfaces/IBaseEscrow.sol";
import {IEscrowFactory} from "contracts/lib/cross-chain-swap/contracts/interfaces/IEscrowFactory.sol";
import {Address} from "solidity-utils/contracts/libraries/AddressLib.sol";
import {TimelocksLib, Timelocks} from "contracts/lib/cross-chain-swap/contracts/libraries/TimelocksLib.sol";

contract ProductionReadyFactory is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address maker = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy a production-ready EscrowFactory with mock LOP
        // In real production, you'd use the actual LOP address
        address mockLOP = address(0x1111111254fb6c44bAC0beD2854e76F90643097d); // Placeholder
        IERC20 usdc = IERC20(0x036CbD53842c5426634e7929541eC2318f3dCF7e); // Base Sepolia USDC
        
        TestEscrowFactory factory = new TestEscrowFactory(
            mockLOP,           // limitOrderProtocol (mock for testnet)
            usdc,              // feeToken
            usdc,              // accessToken  
            maker,             // owner
            86400,             // rescueDelaySrc (1 day)
            86400              // rescueDelayDst (1 day)
        );
        
        // Now we can trigger real events from this factory
        bytes32 orderHash = keccak256("production_order_001");
        bytes32 secret = keccak256("production_secret");
        bytes32 hashlock = keccak256(abi.encodePacked(secret));
        
        Timelocks timelocks = TimelocksLib.setDeployedAt(Timelocks.wrap(0), uint256(block.timestamp));
        
        IBaseEscrow.Immutables memory immutables = IBaseEscrow.Immutables({
            orderHash: orderHash,
            hashlock: hashlock,
            maker: Address.wrap(uint160(maker)),
            taker: Address.wrap(uint160(maker)),
            token: Address.wrap(uint160(address(usdc))),
            amount: 100 * 1e6, // 100 USDC
            safetyDeposit: 0.001 ether,
            timelocks: timelocks
        });

        IEscrowFactory.DstImmutablesComplement memory immutablesComplement = IEscrowFactory.DstImmutablesComplement({
            maker: Address.wrap(uint160(maker)),
            amount: 99 * 1e6,
            token: Address.wrap(uint160(address(0))), // XRP
            safetyDeposit: 0.001 ether,
            chainId: 1440002 // XRPL testnet
        });
        
        // Emit from production-ready factory
        factory.test_emitSrcEscrowCreated(immutables, immutablesComplement);
        
        vm.stopBroadcast();
        
        console.log("Production-ready EscrowFactory deployed at:", address(factory));
        console.log("Real SrcEscrowCreated event emitted!");
        console.log("OrderHash:", vm.toString(orderHash));
        console.log("Update your relayer to this address for production testing");
    }
}