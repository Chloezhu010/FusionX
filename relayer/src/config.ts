import 'dotenv/config';

function getEnvVariable(key: string): string {
    const value = process.env[key];
    if (!value) {
        throw new Error(`Environment variable ${key} is not set.`);
    }
    return value;
}

export const config = {
    ethereum: {
        nodeUrl: getEnvVariable('ETHEREUM_NODE_URL'),
        escrowFactoryAddress: getEnvVariable('ESCROW_FACTORY_ADDRESS'),
    },
    xrpl: {
        nodeUrl: getEnvVariable('XRPL_NODE_URL'),
        relayerWalletSeed: getEnvVariable('RELAYER_XRP_WALLET_SEED'),
        destinationAddress: getEnvVariable('DESTINATION_XRP_ADDRESS'),
    },
}; 