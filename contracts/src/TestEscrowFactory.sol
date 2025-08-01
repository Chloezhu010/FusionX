pragma solidity 0.8.23;

import "cross-chain-swap/EscrowFactory.sol";
import "cross-chain-swap/interfaces/IBaseEscrow.sol";
import "cross-chain-swap/interfaces/IEscrowFactory.sol";

contract TestEscrowFactory is EscrowFactory {
    constructor(
        address limitOrderProtocol,
        IERC20 feeToken,
        IERC20 accessToken,
        address owner, uint32 rescueDelaySrc,
        uint32 rescueDelayDst
    ) EscrowFactory(limitOrderProtocol, feeToken, accessToken, owner, rescueDelaySrc, rescueDelayDst) {}
}
