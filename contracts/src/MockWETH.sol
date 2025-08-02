// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {IERC20} from "openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";

interface IWETH is IERC20 {
    function deposit() external payable;
    function withdraw(uint256) external;
}

contract MockWETH is IWETH {
    string public name = "Wrapped Ether";
    string public symbol = "WETH";
    uint8 public decimals = 18;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    uint256 public totalSupply;
    event Deposit(address indexed dst, uint256 wad);
    event Withdrawal(address indexed src, uint256 wad);
    
    function deposit() external payable {
        balanceOf[msg.sender] += msg.value;
        totalSupply += msg.value;
        emit Deposit(msg.sender, msg.value);
        emit Transfer(address(0), msg.sender, msg.value);
    }
    
    function withdraw(uint256 wad) external {
        require(balanceOf[msg.sender] >= wad, "Insufficient balance");
        balanceOf[msg.sender] -= wad;
        totalSupply -= wad;
        payable(msg.sender).transfer(wad);
        emit Withdrawal(msg.sender, wad);
        emit Transfer(msg.sender, address(0), wad);
    }
    
    function transfer(address to, uint256 value) external returns (bool) {
        require(balanceOf[msg.sender] >= value, "Insufficient balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
    
    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }
    
    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        require(balanceOf[from] >= value, "Insufficient balance");
        require(allowance[from][msg.sender] >= value, "Insufficient allowance");
        
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        
        emit Transfer(from, to, value);
        return true;
    }
}