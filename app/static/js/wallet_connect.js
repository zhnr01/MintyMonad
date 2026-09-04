import { ethers } from "https://cdn.jsdelivr.net/npm/ethers@6.8.1/dist/ethers.min.js";

const walletConnectBtn = document.getElementById('walletConnectBtn');
const walletDisconnectBtn = document.getElementById('walletDisconnectBtn');

if (walletConnectBtn && walletDisconnectBtn) {
    const connected = walletConnectBtn.dataset.connected === 'true';
    walletConnectBtn.hidden = connected;
    walletDisconnectBtn.hidden = !connected;
}

let MONAD_TESTNET = null;

async function loadNetworkConfig() {
    try {
        const resp = await fetch('/api/network_config');
        if (!resp.ok) throw new Error('Failed to fetch network config');
        const cfg = await resp.json();
        // Ensure chainId is a hex string like '0x279f'
        if (typeof cfg.chainId === 'number') cfg.chainId = '0x' + cfg.chainId.toString(16);
        MONAD_TESTNET = cfg;
        return cfg;
    } catch (err) {
        console.error('Could not load network config:', err);
        // Fallback to sensible defaults
        MONAD_TESTNET = {
            chainId: '0x279f', // 10143
            chainName: 'Monad Testnet',
            nativeCurrency: { name: 'Monad', symbol: 'MON', decimals: 18 },
            rpcUrls: ['https://10143.rpc.thirdweb.com'],
            blockExplorerUrls: ['https://testnet.monadexplorer.com/'],
            blockGasLimit: 150000000
        };
        return MONAD_TESTNET;
    }
}

async function connectWallet() {
    if (!window.ethereum) {
        alert('Please install MetaMask or another Ethereum wallet extension!');
        return;
    }
    if (!MONAD_TESTNET) await loadNetworkConfig();

    try {
        let provider = new ethers.BrowserProvider(window.ethereum);

        // Check current network
        const currentNetwork = await provider.getNetwork();

        // Switch to Monad Testnet if not already connected
        // currentNetwork.chainId is bigint; MONAD_TESTNET.chainId may be hex string
        const targetChainId = typeof MONAD_TESTNET.chainId === 'string' ? BigInt(MONAD_TESTNET.chainId) : BigInt(MONAD_TESTNET.chainId);
        if (currentNetwork.chainId !== targetChainId) {
            try {
                await window.ethereum.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: MONAD_TESTNET.chainId }] });
            } catch (error) {
                if (error.code !== 4902) throw error;
                await window.ethereum.request({ method: 'wallet_addEthereumChain', params: [MONAD_TESTNET] });
            }
            provider = new ethers.BrowserProvider(window.ethereum);
        }
        const accounts = await provider.send('eth_requestAccounts', []);

        if (!accounts || accounts.length === 0) {
            throw new Error('No accounts found');
        }

        const signer = await provider.getSigner();
        const walletAddress = await signer.getAddress();

        const truncatedAddress = `${walletAddress.substring(0, 6)}...${walletAddress.substring(walletAddress.length - 4)}`;
        walletConnectBtn.textContent = `Connected: ${truncatedAddress}`;
        walletConnectBtn.disabled = true;

        const csrfResponse = await fetch('/api/csrf-token');
        if (!csrfResponse.ok) throw new Error('Could not start secure wallet verification');
        const { csrf_token } = await csrfResponse.json();
        const nonceResponse = await fetch('/api/nonce', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf_token },
            body: JSON.stringify({ wallet_address: walletAddress }),
        });
        if (!nonceResponse.ok) throw new Error('Could not start wallet verification');
        const { nonce } = await nonceResponse.json();
        const signature = await signer.signMessage(nonce);

        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf_token },
            body: JSON.stringify({
                wallet_address: walletAddress,
                network: 'monad-testnet',
                signature,
                nonce,
            }),
        });

        if (!response.ok) throw new Error('Login failed');
        const data = await response.json();
        console.log('Authentication successful:', data);
        location.reload();

    } catch (error) {
        console.error('Connection error:', error);
        walletConnectBtn.textContent = 'Connect Wallet';

        if (error.code === 4001) {
            alert('Please approve the connection to continue');
        } else {
            alert(`Error: ${error.message}`);
        }
    }
}

function disconnectWallet() {
    fetch('/api/csrf-token')
        .then(response => response.json())
        .then(({ csrf_token }) => fetch('/api/logout', {
            method: 'POST',
            headers: { 'X-CSRF-Token': csrf_token },
        }))
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(json => {
            alert(json.message || 'Logged out successfully');
            location.reload();
        })
        .catch(error => {
            console.error('Logout failed:', error);
            alert('Logout failed. Please try again.');
        });
}

if (walletConnectBtn) walletConnectBtn.addEventListener('click', connectWallet);
if (walletDisconnectBtn) walletDisconnectBtn.addEventListener('click', disconnectWallet);
