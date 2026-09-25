// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// ChainProof 共享测试合约:Day 3 假集成 / Day 7 真集成的统一输入。
// 覆盖:重入 / 未检查返回值 / tx.origin 鉴权 / 时间戳依赖 / unchecked 溢出
contract VulnerableToken {
    mapping(address => uint256) public balances;
    uint256 public totalSupply;
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        totalSupply += msg.value;
    }

    // SWC-107 重入:外部调用之后才更新状态(违反 CEI)
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "insufficient balance");
        (bool ok, ) = msg.sender.call{value: amount}("");
        balances[msg.sender] -= amount;
        totalSupply -= amount;
    }

    // SWC-104 未检查的外部调用返回值
    function transfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount, "insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
        (bool ok, ) = to.call("");
    }

    // SWC-115 tx.origin 鉴权
    function isOwner() public view returns (bool) {
        return tx.origin == owner;
    }

    // SWC-116 时间戳依赖
    function gamble() public view returns (bool) {
        return block.timestamp % 2 == 0;
    }

    // SWC-101 unchecked 溢出
    function unsafeIncrement(uint256 x) public pure returns (uint256) {
        unchecked {
            return x + 1;
        }
    }
}
