// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {IERC20} from "openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";
import {IOrderMixin} from "limit-order-protocol/contracts/interfaces/IOrderMixin.sol";
import {OrderLib} from "limit-order-protocol/contracts/OrderLib.sol";
import {MakerTraitsLib} from "limit-order-protocol/contracts/libraries/MakerTraitsLib.sol";
import {Address} from "solidity-utils/contracts/libraries/AddressLib.sol";
import {TimelocksLib, Timelocks} from "contracts/lib/cross-chain-swap/contracts/libraries/TimelocksLib.sol";
import {IEscrowFactory} from "contracts/lib/cross-chain-swap/contracts/interfaces/IEscrowFactory.sol";

contract CreateLimitOrder is Script {
    // Contract addresses on Base Sepolia
    address constant LOP_ADDRESS = 0x72aB8EcE1ef0E10d5a396015E4996577860D97C5;
    address constant USDC_ADDRESS = 0x036CbD53842c5426634e7929541eC2318f3dCF7e;
    address constant WETH_ADDRESS = 0xbbbA391C85F09a2dBAb5545843191EDF92fcfC49;
    address constant ESCROW_FACTORY = 0xC38DD3B1d0cffA3617ddD8727AC83E9eBDAA5f13;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address maker = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Step 1: Get some USDC tokens (mint or get from faucet)
        // For this demo, we'll assume you have USDC. In reality, you'd need to get testnet USDC
        
        IERC20 usdc = IERC20(USDC_ADDRESS);
        IERC20 weth = IERC20(WETH_ADDRESS);
        
        // Check balances
        uint256 usdcBalance = usdc.balanceOf(maker);
        uint256 wethBalance = weth.balanceOf(maker);
        
        console.log("Maker address:", maker);
        console.log("USDC balance:", usdcBalance);
        console.log("WETH balance:", wethBalance);
        
        // Step 2: Approve LOP to spend USDC
        uint256 orderAmount = 5 * 1e6; // 5 USDC (6 decimals) - less than your 10 USDC balance
        if (usdcBalance >= orderAmount) {
            usdc.approve(LOP_ADDRESS, orderAmount);
            console.log("Approved", orderAmount, "USDC to LOP");
        } else {
            console.log("Insufficient USDC balance. Need to get testnet USDC first.");
            vm.stopBroadcast();
            return;
        }
        
        // Step 3: Create limit order data
        // This creates an order to swap 100 USDC for WETH, but we'll configure it 
        // to use the EscrowFactory as a post-interaction
        
        bytes32 orderHash = keccak256("cross_chain_order_001");
        bytes32 secret = keccak256("secret_for_xrpl_swap");
        bytes32 hashlock = keccak256(abi.encodePacked(secret));
        
        // Create timelocks for cross-chain swap
        Timelocks timelocks = TimelocksLib.setDeployedAt(Timelocks.wrap(0), uint256(block.timestamp));
        
        // Prepare extra data for EscrowFactory postInteraction
        IEscrowFactory.ExtraDataArgs memory extraDataArgs = IEscrowFactory.ExtraDataArgs({
            hashlockInfo: hashlock,
            dstChainId: 1440002, // XRPL testnet
            dstToken: Address.wrap(uint160(address(0))), // Native XRP
            deposits: (uint256(0.001 ether) << 128) | uint256(0.001 ether), // safety deposits
            timelocks: timelocks
        });
        
        // Encode extra data
        bytes memory extraData = abi.encode(extraDataArgs);
        
        console.log("Created limit order configuration");
        console.log("OrderHash:", vm.toString(orderHash));
        console.log("Hashlock:", vm.toString(hashlock));
        console.log("Secret (for demo):", vm.toString(secret));
        
        vm.stopBroadcast();
        
        console.log("=== NEXT STEPS ===");
        console.log("1. Get testnet USDC from faucet if balance is 0");
        console.log("2. The order is configured but not yet submitted to LOP");
        console.log("3. To complete, you need to call fillOrder on the LOP with proper signature");
        console.log("4. This will trigger the EscrowFactory postInteraction");
        console.log("5. Which will emit SrcEscrowCreated event for your relayer");
    }
}