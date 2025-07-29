// SPDX-License-Identifier: MIT

pragma solidity 0.8.23;

import {Ownable} from "openzeppelin-contracts/contracts/access/Ownable.sol";
// import {IOrderMixin} from "limit-order-protocol/contracts/interfaces/IOrderMixin.sol";
// import {TakerTraits} from "limit-order-protocol/contracts/libraries/TakerTraitsLib.sol";

import {IResolverExample} from "../lib/cross-chain-swap/contracts/interfaces/IResolverExample.sol";
import {RevertReasonForwarder} from "../lib/cross-chain-swap/lib/solidity-utils/contracts/libraries/RevertReasonForwarder.sol";
import {IEscrowFactory} from "../lib/cross-chain-swap/contracts/interfaces/IEscrowFactory.sol";
import {IBaseEscrow} from "../lib/cross-chain-swap/contracts/interfaces/IBaseEscrow.sol";
import {TimelocksLib, Timelocks} from "../lib/cross-chain-swap/contracts/libraries/TimelocksLib.sol";
import {Address} from "solidity-utils/contracts/libraries/AddressLib.sol";
import {IEscrow} from "../lib/cross-chain-swap/contracts/interfaces/IEscrow.sol";
import {ImmutablesLib} from "../lib/cross-chain-swap/contracts/libraries/ImmutablesLib.sol";
import {IXrplBridge} from "./interfaces/IXrplBridge.sol";

/**
 * @title Sample implementation of a Resolver contract for cross-chain swap.
 * @dev It is important when deploying an escrow on the source chain to send the safety deposit and deploy the escrow in the same
 * transaction, since the address of the escrow depends on the block.timestamp.
 * You can find sample code for this in the {ResolverExample-deploySrc}.
 *
 * @custom:security-contact security@fusionx.io
 */
contract Resolver is Ownable {
    using ImmutablesLib for IBaseEscrow.Immutables;
    using TimelocksLib for Timelocks;

    error InvalidLength();
    error LengthMismatch();
    error XrplBridgeNotActive();
    error InvalidXrplDestination();

    IEscrowFactory private immutable _FACTORY;
    // IOrderMixin private immutable _LOP;
    IXrplBridge private immutable _XRPL_BRIDGE;

    // constructor(IEscrowFactory factory, IOrderMixin lop, address initialOwner) Ownable(initialOwner) {
    constructor(IEscrowFactory factory, IXrplBridge xrplBridge, address initialOwner) Ownable(initialOwner) {
        _FACTORY = factory;
        // _LOP = lop;
        _XRPL_BRIDGE = xrplBridge;
    }

    receive() external payable {} // solhint-disable-line no-empty-blocks

    /**
     * @notice See {IResolverExample-deploySrc}.
     */
    function deploySrc(
        IBaseEscrow.Immutables calldata immutables,
        uint256 amount,
        string calldata xrplDestination,
        bytes calldata xrplData
    ) external payable onlyOwner {
        // Validate XRPL destination address
        if (bytes(xrplDestination).length == 0) revert InvalidXrplDestination();
        
        // Check if XRPL bridge is active
        if (!_XRPL_BRIDGE.isActive()) revert XrplBridgeNotActive();

        IBaseEscrow.Immutables memory immutablesMem = immutables;
        // 1. create source escrow with timestamp
        immutablesMem.timelocks = TimelocksLib.setDeployedAt(immutables.timelocks, block.timestamp);
        address computed = _FACTORY.addressOfEscrowSrc(immutablesMem);
        
        // 2. send safety deposit to the escrow
        (bool success,) = address(computed).call{value: immutablesMem.safetyDeposit}("");
        if (!success) revert IBaseEscrow.NativeTokenSendingFailure();

        // 3. initiate XRPL transfer through bridge
        _XRPL_BRIDGE.initiateTransfer(computed, amount, xrplDestination, xrplData);
    }

    /**
     * @notice See {IResolverExample-deployDst}.
     */
    function deployDst(IBaseEscrow.Immutables calldata dstImmutables, uint256 srcCancellationTimestamp) external onlyOwner payable {
        _FACTORY.createDstEscrow{value: msg.value}(dstImmutables, srcCancellationTimestamp);
    }

    /**
     * @notice Complete XRPL to ETH transfer
     */
    function completeXrplTransfer(
        address escrowAddress,
        uint256 amount,
        string calldata xrplSource,
        bytes calldata proof
    ) external onlyOwner {
        _XRPL_BRIDGE.completeTransfer(escrowAddress, amount, xrplSource, proof);
    }

    function withdraw(IEscrow escrow, bytes32 secret, IBaseEscrow.Immutables calldata immutables) external {
        escrow.withdraw(secret, immutables);
    }


    function cancel(IEscrow escrow, IBaseEscrow.Immutables calldata immutables) external {
        escrow.cancel(immutables);
    }

    /**
     * @notice See {IResolverExample-arbitraryCalls}.
     */
    function arbitraryCalls(address[] calldata targets, bytes[] calldata arguments) external onlyOwner {
        uint256 length = targets.length;
        if (targets.length != arguments.length) revert LengthMismatch();
        for (uint256 i = 0; i < length; ++i) {
            // solhint-disable-next-line avoid-low-level-calls
            (bool success,) = targets[i].call(arguments[i]);
            if (!success) RevertReasonForwarder.reRevert();
        }
    }
}
