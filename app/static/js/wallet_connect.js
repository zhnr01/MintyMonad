import { ethers } from "https://cdn.jsdelivr.net/npm/ethers@6.8.1/dist/ethers.min.js";

const walletConnectBtn = document.getElementById('walletConnectBtn');
const walletDisconnectBtn = document.getElementById('walletDisconnectBtn');

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
    // Ensure network configuration is loaded from backend
    if (!MONAD_TESTNET) await loadNetworkConfig();

    try {
        // First, explicitly request permissions to trigger the popup every time
        await window.ethereum.request({
            method: 'wallet_requestPermissions',
            params: [{ eth_accounts: {} }],
        });

        const provider = new ethers.BrowserProvider(window.ethereum);

        // Check current network
        const currentNetwork = await provider.getNetwork();

        // Switch to Monad Testnet if not already connected
        // currentNetwork.chainId is bigint; MONAD_TESTNET.chainId may be hex string
        const targetChainId = typeof MONAD_TESTNET.chainId === 'string' ? BigInt(MONAD_TESTNET.chainId) : BigInt(MONAD_TESTNET.chainId);
        if (currentNetwork.chainId !== targetChainId) {
            try {
                await window.ethereum.request({
                    method: 'wallet_addEthereumChain',
                    params: [MONAD_TESTNET]
                });
            } catch (switchError) {
                if (switchError.code === 4902) {
                    console.error('Monad Testnet not configured in wallet (code 4902)');
                }
                throw new Error('Failed to add/switch to Monad Testnet');
            }
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

        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wallet_address: walletAddress,
                network: 'monad-testnet'
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
    fetch('/api/logout')
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

walletConnectBtn.addEventListener('click', connectWallet);
walletDisconnectBtn.addEventListener('click', disconnectWallet);
