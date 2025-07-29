// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

interface IXrplOracle {
    function verifyXrplPayment(
        string calldata txHash, 
        bytes32 secret, 
        string calldata destination, 
        string calldata amount
    ) external view returns (bool);
}

contract MockXrplOracle is IXrplOracle {
    // For testing purposes, always return true
    // In production, this would verify actual XRPL transactions
    function verifyXrplPayment(
        string calldata txHash, 
        bytes32 secret, 
        string calldata destination, 
        string calldata amount
    ) external pure returns (bool) {
        // Mock implementation - always return true for testing
        return true;
    }
} 