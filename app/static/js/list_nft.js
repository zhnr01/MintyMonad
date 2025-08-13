import { ethers } from "https://cdn.jsdelivr.net/npm/ethers@6.8.1/dist/ethers.min.js";

async function listNFTOnMarketplace() {
    document.getElementById('listButton').disabled = true;
    document.getElementById('listButton').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Listing...';
    //e.preventDefault();
    // 1. Get user inputs
    const contractAddress = document.getElementById('address').textContent.trim();
    const tokenId = document.getElementById('id').textContent.trim();
    const price = document.getElementById('nftPrice').value.trim(); // Price in $MON
    if (!contractAddress || !tokenId || !price) {
        alert("Please fill all fields!");
        return;
    }

    // 2. Check if MetaMask (or another wallet) is installed
    if (!window.ethereum) {
        alert("Please install MetaMask!");
        return;
    }

    try {
        // 3. Connect to the wallet
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();
        const userAddress = await signer.getAddress();

        // 4. Load the Marketplace contract ABI
        // (You need to store this ABI in your frontend, e.g., in a `contracts` folder)
        const response = await fetch('/api/marketplace_abi');
        console.log(response.body);
        const marketplaceABI = await response.json();

        // 5. Initialize the contract
        const marketplaceAddress = "0x7dA4Bf6D0EdC392C82D6C8A5aac414810689B9AE"; // Your deployed Marketplace contract address
        const marketplaceContract = new ethers.Contract(
            marketplaceAddress,
            marketplaceABI,
            signer
        );

        // 6. Convert price to Wei (1 $MON = 10^18 wei)
        const priceWei = ethers.parseEther(price);

        // 7. Call the `setNFTPrice` function
        const tx = await marketplaceContract.setNFTPrice(
            contractAddress,
            tokenId,
            priceWei
        );
        
        // 8. Wait for transaction confirmation
        await tx.wait();

        alert("🎉 NFT listed successfully! TX Hash: " + tx.hash);
        console.log("Transaction:", tx);
        document.getElementById('listButton').textContent = 'Listed!';

    } catch (error) {
        console.error("Listing failed:", error);
        alert("❌ Error: " + (error.reason || error.message));
    }
}

document.getElementById('listButton').addEventListener('click', listNFTOnMarketplace);