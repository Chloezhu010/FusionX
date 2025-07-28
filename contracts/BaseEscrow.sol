// SPDX-License-Identifier: MIT

pragma solidity ^0.8.23;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

struct Timelocks {
    uint256 srcWithdrawal;      // When resolver can withdraw from source
    uint256 srcCancellation;    // When source escrow can be cancelled
    uint256 dstWithdrawal;      // When user can withdraw from destination
    uint256 dstCancellation;    // When destination escrow can be cancelled
}

abstract contract BaseEscrow is ReentrancyGuard {
    using SafeERC20 for IERC20;
    
    error InvalidCaller();
    error InvalidSecret();
    error InvalidTime();
    error InvalidAmount();
    error NativeTokenSendingFailure();
    
    event FundsRescued(address token, uint256 amount);
    event Withdrawn(bytes32 indexed orderHash, address indexed taker, uint256 amount);
    event Cancelled(bytes32 indexed orderHash);
    
    modifier onlyAfter(uint256 timestamp) {
        if (block.timestamp < timestamp) revert InvalidTime();
        _;
    }
    
    modifier onlyBefore(uint256 timestamp) {
        if (block.timestamp >= timestamp) revert InvalidTime();
        _;
    }
    
    function _keccakBytes32(bytes32 secret) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(secret));
    }
    
    function _uniTransfer(address token, address to, uint256 amount) internal {
        if (token == address(0)) {
            (bool success,) = to.call{value: amount}("");
            if (!success) revert NativeTokenSendingFailure();
        } else {
            IERC20(token).safeTransfer(to, amount);
        }
    }
} 