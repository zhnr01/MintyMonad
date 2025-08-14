import { ethers } from "https://cdn.jsdelivr.net/npm/ethers@6.8.1/dist/ethers.min.js";


const contract_response = await fetch('/api/marketplace_contract_address');
const marketplace_contract_dict = await contract_response.json();
const MARKETPLACE_ADDRESS = marketplace_contract_dict['contract_address']

// ERC-721 minimal ABI for approval + interface check
const ERC721_ABI = [
    "function approve(address to, uint256 tokenId) external",
    "function supportsInterface(bytes4 interfaceId) external view returns (bool)"
];

async function approveNFTFromWallet() {
    try {
        // Get NFT details from the page
        const nftContractAddress = document.getElementById('address').textContent.trim();
        const tokenId = document.getElementById('id').textContent.trim();

        if (!window.ethereum) {
            throw new Error("Please connect a wallet");
        }

        // Request account access if needed
        await window.ethereum.request({ method: 'eth_requestAccounts' });

        // Setup provider and signer
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();

        // Create contract instance
        const nftContract = new ethers.Contract(nftContractAddress, ERC721_ABI, signer);

        // Check if the token contract is ERC-721
        const isERC721 = await nftContract.supportsInterface("0x80ac58cd");
        if (!isERC721) {
            alert("This token is not an ERC-721 NFT. Approval not supported.");
            return;
        }

        console.log(`Requesting approval for token ID ${tokenId} from contract ${nftContractAddress}...`);

        // Send approval transaction
        const tx = await nftContract.approve(MARKETPLACE_ADDRESS, tokenId);
        console.log("Transaction sent:", tx.hash);

        // Add link to explorer
        const txLink = document.createElement('span');
        txLink.innerHTML = `<a href='https://testnet.monadexplorer.com/tx/${tx.hash}' target="_blank">View on Explorer</a>`;
        document.getElementsByClassName('card-footer')[0].innerHTML = '';
        document.getElementsByClassName('card-footer')[0].append(txLink);

        // Wait for confirmation
        const receipt = await tx.wait();
        console.log("Approval confirmed in block:", receipt.blockNumber);

        return receipt;

    } catch (err) {
        console.error("Approval failed:", err);

        if (err.code === 4001) {
            alert("Approval was cancelled by user");
        } else if (err.code === "UNSUPPORTED_OPERATION") {
            alert("Wallet connection issue. Please try reconnecting your wallet.");
        } else {
            alert("Approval failed: " + (err.reason || err.message));
        }

        throw err;
    }
}

// Event listener with loading state
const approveBtn = document.getElementById('approve');
approveBtn.addEventListener('click', async function () {
    try {
        approveBtn.disabled = true;
        approveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Approving...';

        await approveNFTFromWallet();

    } finally {
        approveBtn.textContent = 'Approved';
        document.getElementById('listButton').style.display = 'block';
    }
});
