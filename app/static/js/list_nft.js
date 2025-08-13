import { ethers } from "https://cdn.jsdelivr.net/npm/ethers@6.8.1/dist/ethers.min.js";

async function listNFTOnMarketplace() {
    const listButton = document.getElementById('listButton');
    listButton.disabled = true;
    listButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Listing...';

    const contractAddress = document.getElementById('address').textContent.trim();
    const tokenId = document.getElementById('id').textContent.trim();
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
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();

        const response = await fetch('/api/marketplace_abi');
        const marketplaceABI = await response.json();

        const marketplaceAddress = "0x7dA4Bf6D0EdC392C82D6C8A5aac414810689B9AE";
        const marketplaceContract = new ethers.Contract(marketplaceAddress, marketplaceABI, signer);

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
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();

        const response = await fetch('/api/marketplace_abi');
        const marketplaceABI = await response.json();

        const marketplaceAddress = "0x7dA4Bf6D0EdC392C82D6C8A5aac414810689B9AE";
        const marketplaceContract = new ethers.Contract(marketplaceAddress, marketplaceABI, signer);

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
