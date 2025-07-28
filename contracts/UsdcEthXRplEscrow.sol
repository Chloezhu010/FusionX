// SPDX-License-Identifier: MIT

pragma solidity ^0.8.23;

import "./BaseEscrow.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IXrplOracle {
    function verifyXrplPayment(
        string calldata txHash, 
        bytes32 secret, 
        string calldata destination, 
        string calldata amount
    ) external view returns (bool);
}

contract UsdcEthXrplEscrow is BaseEscrow, Ownable {
    using SafeERC20 for IERC20;
    
    struct UsdcSwapImmutables {
        bytes32 orderHash;
        bytes32 hashlock;
        address maker;              // ETH user address
        address taker;              // Resolver address
        string xrplDestination;     // XRPL address
        address usdcToken;          // ETH USDC contract address
        uint256 amount;             // ETH USDC amount (6 decimals)
        uint256 safetyDeposit;      // ETH safety deposit
        string xrplCurrency;        // "USD" or "USDC"
        string xrplIssuer;          // XRPL USDC issuer address
        string xrplAmount;          // XRPL amount format "1.000000"
        Timelocks timelocks;
    }
    
    // Store escrow data
    mapping(bytes32 => UsdcSwapImmutables) public escrows;
    mapping(bytes32 => bool) public completed;
    
    // Oracle for XRPL verification
    IXrplOracle public xrplOracle;
    
    event EscrowCreated(
        bytes32 indexed orderHash,
        address indexed maker,
        address indexed taker,
        string xrplDestination,
        uint256 usdcAmount,
        string xrplCurrency,
        string xrplIssuer
    );
    
    constructor(address _xrplOracle) Ownable(msg.sender) {
        xrplOracle = IXrplOracle(_xrplOracle);
    }
    
    function setXrplOracle(address _xrplOracle) external onlyOwner {
        xrplOracle = IXrplOracle(_xrplOracle);
    }
    
    function createEscrow(UsdcSwapImmutables calldata params) external payable nonReentrant {
        require(params.amount > 0, "Invalid amount");
        require(msg.value >= params.safetyDeposit, "Insufficient safety deposit");
        require(escrows[params.orderHash].orderHash == bytes32(0), "Escrow already exists");
        
        // Transfer USDC from maker to this contract
        IERC20(params.usdcToken).safeTransferFrom(
            params.maker,
            address(this),
            params.amount
        );
        
        // Store escrow parameters
        escrows[params.orderHash] = params;
        
        emit EscrowCreated(
            params.orderHash,
            params.maker,
            params.taker,
            params.xrplDestination,
            params.amount,
            params.xrplCurrency,
            params.xrplIssuer
        );
    }
    
    function withdraw(
        bytes32 secret,
        bytes32 orderHash,
        string calldata xrplTxHash  // Proof XRPL payment was made
    ) external 
        nonReentrant
        onlyAfter(escrows[orderHash].timelocks.srcWithdrawal)
        onlyBefore(escrows[orderHash].timelocks.srcCancellation)
    {
        UsdcSwapImmutables memory params = escrows[orderHash];
        require(params.orderHash != bytes32(0), "Escrow not found");
        require(msg.sender == params.taker, "Only taker can withdraw");
        require(!completed[orderHash], "Already completed");
        require(_keccakBytes32(secret) == params.hashlock, "Invalid secret");
        
        // Verify XRPL payment occurred through oracle
        require(
            xrplOracle.verifyXrplPayment(
                xrplTxHash, 
                secret, 
                params.xrplDestination, 
                params.xrplAmount
            ), 
            "Invalid XRPL payment"
        );
        
        completed[orderHash] = true;
        
        // Transfer USDC to resolver
        IERC20(params.usdcToken).safeTransfer(msg.sender, params.amount);
        
        // Return safety deposit to resolver
        (bool success,) = msg.sender.call{value: params.safetyDeposit}("");
        require(success, "Safety deposit transfer failed");
        
        emit Withdrawn(params.orderHash, msg.sender, params.amount);
    }
    
    function cancel(bytes32 orderHash) external 
        nonReentrant
        onlyAfter(escrows[orderHash].timelocks.srcCancellation) 
    {
        UsdcSwapImmutables memory params = escrows[orderHash];
        require(params.orderHash != bytes32(0), "Escrow not found");
        require(!completed[orderHash], "Already completed");
        
        completed[orderHash] = true;
        
        // Return USDC to maker
        IERC20(params.usdcToken).safeTransfer(params.maker, params.amount);
        
        // Return safety deposit to maker
        (bool success,) = params.maker.call{value: params.safetyDeposit}("");
        require(success, "Safety deposit transfer failed");
        
        emit Cancelled(params.orderHash);
    }
    
    function getEscrow(bytes32 orderHash) external view returns (UsdcSwapImmutables memory) {
        return escrows[orderHash];
    }
    
    function isCompleted(bytes32 orderHash) external view returns (bool) {
        return completed[orderHash];
    }
}