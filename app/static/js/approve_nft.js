import { ethers } from "https://cdn.jsdelivr.net/npm/ethers@6.8.1/dist/ethers.min.js";


const contract_response = await fetch('/api/marketplace_contract_address');
const marketplace_contract_dict = await contract_response.json();
const MARKETPLACE_ADDRESS = marketplace_contract_dict['contract_address']

const ERC721_ABI = [
    "function approve(address to, uint256 tokenId) external",
    "function supportsInterface(bytes4 interfaceId) external view returns (bool)"
];

async function approveNFTFromWallet() {
    try {
        const nftContractAddress = document.getElementById('contract_address').textContent.trim();
        const tokenId = document.getElementById('token_id').textContent.trim();

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

        const txLink = document.createElement('a');
        txLink.href = `https://testnet.monadexplorer.com/tx/${tx.hash}`;
        txLink.target = '_blank';
        txLink.rel = 'noopener noreferrer';
        txLink.textContent = 'View on Explorer';
        const footer = document.querySelector('.card-footer');
        if (footer) footer.replaceChildren(txLink);

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

const approveBtn = document.getElementById('approve');
if (approveBtn) approveBtn.addEventListener('click', async function () {
    try {
        approveBtn.disabled = true;
        approveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Approving...';

        await approveNFTFromWallet();

    } catch {
        approveBtn.disabled = false;
        approveBtn.textContent = 'Approve Listing';
    } finally {
        if (!approveBtn.disabled) return;
        approveBtn.textContent = 'Approved';
        const listButton = document.getElementById('listButton');
        if (listButton) listButton.hidden = false;
    }
});
