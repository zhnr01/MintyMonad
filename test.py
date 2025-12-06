from web3 import Web3
import json

# ======= CONFIG =======
MONAD_RPC = "https://testnet-rpc.monad.xyz"
MARKETPLACE_ADDRESS = '0x7dA4Bf6D0EdC392C82D6C8A5aac414810689B9AE'  # your deployed contract address

# Load ABI
with open("contracts/NFTMarketplace.abi.json") as f:
    ABI = json.load(f)

# Connect to Monad RPC
w3 = Web3(Web3.HTTPProvider(MONAD_RPC))
assert w3.is_connected(), "Failed to connect to Monad RPC"

# Create contract instance
marketplace = w3.eth.contract(address=Web3.to_checksum_address(MARKETPLACE_ADDRESS), abi=ABI)

def get_nft_price(nft_address: str, token_id: int) -> float:
    nft_address = Web3.to_checksum_address(nft_address)
    price_wei = marketplace.functions.getPrice(nft_address, token_id).call()
    price_mon = w3.from_wei(price_wei, 'ether')  # Convert wei to MON
    return price_mon

def get_all_listed_nfts():
    # This returns two parallel lists: addresses and token IDs
    nft_addresses, token_ids = marketplace.functions.getAllListedNFTs().call()
    results = []
    for nft_address, token_id in zip(nft_addresses, token_ids):
        nft_address = Web3.to_checksum_address(nft_address)
        price = get_nft_price(nft_address, token_id)
        results.append({
            "contract_address": nft_address,
            "token_id": token_id,
            "price_mon": price
        })
    return results

# Example usage:
if __name__ == "__main__":
    listed_nfts = get_all_listed_nfts()
    for nft in listed_nfts:
        print(f"NFT {nft['token_id']} at {nft['contract_address']} is listed for {nft['price_mon']} MON")




