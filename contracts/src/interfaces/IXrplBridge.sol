// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

/**
 * @title XRPL Bridge Interface
 * @dev Interface for XRPL bridge contract that handles cross-chain transfers
 */
interface IXrplBridge {
    /**
     * @notice Initiates a transfer from Ethereum to XRPL
     * @param escrowAddress The escrow contract address
     * @param amount The amount to transfer
     * @param xrplDestination The XRPL destination address
     * @param xrplData Additional XRPL-specific data
     */
    function initiateTransfer(
        address escrowAddress,
        uint256 amount,
        string calldata xrplDestination,
        bytes calldata xrplData
    ) external;

    /**
     * @notice Completes a transfer from XRPL to Ethereum
     * @param escrowAddress The escrow contract address
     * @param amount The amount to transfer
     * @param xrplSource The XRPL source address
     * @param proof The proof of XRPL transaction
     */
    function completeTransfer(
        address escrowAddress,
        uint256 amount,
        string calldata xrplSource,
        bytes calldata proof
    ) external;

    /**
     * @notice Gets the XRPL bridge status
     * @return isActive Whether the bridge is active
     */
    function isActive() external view returns (bool);

    /**
     * @notice Gets the XRPL server URL
     * @return serverUrl The XRPL server URL
     */
    function getXrplServer() external view returns (string memory);
} 