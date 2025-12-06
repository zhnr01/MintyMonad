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

    const targetChainId = typeof MONAD_TESTNET.chainId === 'string' ? BigInt(MONAD_TESTNET.chainId) : BigInt(MONAD_TESTNET.chainId);
    if (network.chainId !== targetChainId) {
        await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [MONAD_TESTNET]
        });
    }
    return provider;
}

async function listNFTOnMarketplace() {
    const listButton = document.getElementById('listButton');
    listButton.disabled = true;
    listButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Listing...';

    const contractAddress = document.getElementById('contract_address').textContent.trim();
    const tokenId = document.getElementById('token_id').textContent.trim();
    const price = document.getElementById('nftPrice').value.trim();

    if (!contractAddress || !tokenId || !price) {
        alert("Please fill all fields!");
        listButton.disabled = false;
        listButton.textContent = 'List NFT';
        return;
    }

    if (!window.ethereum) {
        alert("Please install MetaMask!");
        listButton.disabled = false;
        listButton.textContent = 'List NFT';
        return;
    }

    try {
        const provider = await ensureMonadNetwork();
        const signer = await provider.getSigner();

        const response = await fetch('/api/marketplace_abi');
        if (!response.ok) throw new Error('Failed to load marketplace ABI');
        const marketplaceABI = await response.json();

        const contract_response = await fetch('/api/marketplace_contract_address');
        if (!contract_response.ok) throw new Error('Failed to load marketplace address');
        const marketplace_contract_dict = await contract_response.json()
        const marketplace_contract = marketplace_contract_dict['contract_address']
        const marketplaceContract = new ethers.Contract(marketplace_contract, marketplaceABI, signer);

        const priceWei = ethers.parseEther(price);

        const tx = await marketplaceContract.setNFTPrice(contractAddress, tokenId, priceWei);
        await tx.wait();

        alert("🎉 NFT listed successfully! TX Hash: " + tx.hash);
        listButton.textContent = 'Listed!';

    } catch (error) {
        console.error("Listing failed:", error);
        alert("❌ Error: " + (error.reason || error.message));
        listButton.disabled = false;
        listButton.textContent = 'List NFT';
    }
}

async function unlistNFTOnMarketplace(event) {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Unlisting...';
    const contractAddress = btn.getAttribute('data-contract');
    const tokenId = btn.getAttribute('data-tokenid');
    console.log(contractAddress);
    console.log(tokenId);

    if (!contractAddress || !tokenId) {
        alert("Invalid NFT details!");
        btn.disabled = false;
        btn.textContent = 'Unlist';
        return;
    }

    if (!window.ethereum) {
        alert("Please install MetaMask!");
        btn.disabled = false;
        btn.textContent = 'Unlist';
        return;
    }

    try {
        const provider = await ensureMonadNetwork();
        const signer = await provider.getSigner();

        const response = await fetch('/api/marketplace_abi');
        const marketplaceABI = await response.json();
        const contract_response = await fetch('/api/marketplace_contract_address');
        const marketplace_contract_dict = await contract_response.json()
        const marketplace_contract = marketplace_contract_dict['contract_address']
        const marketplaceContract = new ethers.Contract(marketplace_contract, marketplaceABI, signer);

        const tx = await marketplaceContract.unlistNFT(contractAddress, tokenId);
        await tx.wait();

        alert("✅ NFT unlisted successfully! TX Hash: " + tx.hash);
        btn.textContent = 'Unlisted';
        btn.disabled = true;
        location.reload();

    } catch (error) {
        console.error("Unlisting failed:", error);
        alert("❌ Error: " + (error.reason || error.message));
        btn.disabled = false;
        btn.textContent = 'Unlist';
    }
}

document.addEventListener('click', function(event) {
  if (event.target.classList.contains('unlistBtn')) {
    unlistNFTOnMarketplace(event);
  } else if (event.target.id === 'listButton') {
    listNFTOnMarketplace(event);
  }
});
