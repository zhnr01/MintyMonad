import { ethers } from "https://cdn.jsdelivr.net/npm/ethers@6.8.1/dist/ethers.min.js";

let MONAD_TESTNET = null;

async function loadNetworkConfig() {
    try {
        const resp = await fetch('/api/network_config');
        if (!resp.ok) throw new Error('Failed to fetch network config');
        const cfg = await resp.json();
        if (typeof cfg.chainId === 'number') cfg.chainId = '0x' + cfg.chainId.toString(16);
        MONAD_TESTNET = cfg;
        return cfg;
    } catch (err) {
        console.error('Could not load network config:', err);
        MONAD_TESTNET = {
            chainId: '0x279f', 
            chainName: 'Monad Testnet',
            nativeCurrency: { name: 'Monad', symbol: 'MON', decimals: 18 },
            rpcUrls: ['https://testnet-rpc.monad.xyz'],
            blockExplorerUrls: ['https://testnet.monadexplorer.com/'],
            blockGasLimit: 150000000
        };
        return MONAD_TESTNET;
    }
}

async function ensureMonadNetwork() {
    if (!MONAD_TESTNET) await loadNetworkConfig();
    if (!window.ethereum) throw new Error("Please install MetaMask or a Monad-compatible wallet");

    const provider = new ethers.BrowserProvider(window.ethereum);
    const network = await provider.getNetwork();

    // If not already on Monad Testnet, switch
    const targetChainId = typeof MONAD_TESTNET.chainId === 'string' ? BigInt(MONAD_TESTNET.chainId) : BigInt(MONAD_TESTNET.chainId);
    if (network.chainId !== targetChainId) {
        await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [MONAD_TESTNET]
        });
    }
    return provider;
}

document.addEventListener('click', async function (e) {
    if (e.target.classList.contains('acceptProposal')) {
        e.preventDefault();

        const button = e.target;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Accepting...'
        const contractAddress = button.getAttribute('data-contract');
        const tokenId = button.getAttribute('data-tokenid');
        const buyerAddress = button.getAttribute('data-buyer');

        try {
            const provider = await ensureMonadNetwork();
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            const signer = await provider.getSigner();

            const response = await fetch('/api/marketplace_abi');
            if (!response.ok) throw new Error('Failed to load marketplace ABI');
            const contractAbi = await response.json();
            const contract_response = await fetch('/api/marketplace_contract_address');
            const marketplace_contract_dict = await contract_response.json()
            const MARKETPLACE_ADDRESS = marketplace_contract_dict['contract_address']
            const contract = new ethers.Contract(MARKETPLACE_ADDRESS, contractAbi, signer);

            const tx = await contract.acceptNFTProposal(
                contractAddress,
                tokenId,
                buyerAddress
            );

            console.log("Transaction sent:", tx.hash);
            alert(`Proposal accepted. TX: ${tx.hash}`);

            await tx.wait();
            alert(`Proposal confirmed on Monad network!`);
            button.innerHTML = 'Confirmed'
        } catch (err) {
            console.error(err);
            alert("Error submitting offer: " + err.message);
            button.innerHTML = 'Accept Proposal'
            button.disabled = false;
        }
    }
});
