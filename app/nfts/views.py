import json
from flask import jsonify, render_template, current_app, request, session, url_for
from . import nfts  
from urllib.parse import unquote
import requests
from web3 import Web3


@nfts.route('/list', methods=['GET'])
def list_nft():
    contract_address = unquote(request.args.get('contract_address', ''))
    token_id = unquote(request.args.get('token_id', ''))
    return render_template('list_nft.html', contract_address=contract_address, token_id=token_id)

@nfts.route("/mine", methods=["GET"])
def my_nfts():
    wallet_address = session.get('wallet_address')
    if not wallet_address:
        return jsonify({"error": "Wallet address is required"}), 400

    # Fetch owned NFTs from Alchemy
    params = {
        "owner": wallet_address,
        "withMetadata": "true",
        "pageSize": 100
    }
    headers = {"accept": "application/json"}

    try:
        response = requests.get(current_app.config.get('ALCHEMY_URL'), headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        owned_nfts = []
        for nft in data.get("ownedNfts", []):
            if nft["tokenType"] != "ERC721":
                continue
            owned_nfts.append({
                "name": nft['contract']['name'],
                "symbol": nft['contract']['symbol'],
                "contract_address": nft['contract']['address'].lower(),
                "image_url": nft.get('image', {}).get('thumbnailUrl') or url_for('static', filename='images/dummy.png'),
                "token_id": nft['tokenId']
            })

        # Now fetch all listed NFTs from marketplace and build a lookup set
        rpc_url = current_app.config.get('MONAD_RPC_URL')
        marketplace_address = Web3.to_checksum_address(
            current_app.config.get('NFT_MARKETPLACE_CONTRACT_ADDRESS')
        )
        with open('/home/byte/Desktop/minty monad/app/static/NFTMarketplace.abi.json') as f:
            marketplace_abi = json.load(f)

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        marketplace_contract = w3.eth.contract(address=marketplace_address, abi=marketplace_abi)
        listed_nfts, listed_token_ids = marketplace_contract.functions.getAllListedNFTs().call()

        # Build a set of (contract_address.lower(), token_id) for quick lookup
        listed_set = set(
            (addr.lower(), tid)
            for addr, tid in zip(listed_nfts, listed_token_ids)
        )

        # Add 'listed' flag to each owned NFT
        for nft in owned_nfts:
            key = (nft['contract_address'].lower(), int(nft['token_id']))
            nft['listed'] = key in listed_set

        return render_template('my-nfts.html', nfts=owned_nfts)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@nfts.route('/marketplace-data', methods=['GET'])
def marketplace_data():
    try:
        rpc_url = current_app.config.get('MONAD_RPC_URL')
        marketplace_address = Web3.to_checksum_address(
            current_app.config.get('NFT_MARKETPLACE_CONTRACT_ADDRESS')
        )
        with open('/home/byte/Desktop/minty monad/app/static/NFTMarketplace.abi.json') as f:
            marketplace_abi = json.load(f)

        erc721_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "tokenId", "type": "uint256"}],
                "name": "tokenURI",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "tokenId", "type": "uint256"}],
                "name": "ownerOf",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            }
        ]

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        marketplace_contract = w3.eth.contract(address=marketplace_address, abi=marketplace_abi)
        listed_nfts, listed_token_ids = marketplace_contract.functions.getAllListedNFTs().call()

        results = []
        for nft_address, token_id in zip(listed_nfts, listed_token_ids):
            nft_address = Web3.to_checksum_address(nft_address)
            nft_contract = w3.eth.contract(address=nft_address, abi=erc721_abi)

            price_wei = marketplace_contract.functions.getPrice(nft_address, token_id).call()

            try:
                symbol = nft_contract.functions.symbol().call()
            except Exception:
                symbol = "Unknown"

            try:
                token_uri = nft_contract.functions.tokenURI(token_id).call()
                if token_uri.startswith("ipfs://"):
                    token_uri = token_uri.replace("ipfs://", "https://ipfs.io/ipfs/")
                metadata = requests.get(token_uri).json()
                image_url = metadata.get("image", url_for('static', filename='images/dummy.png'))
                if image_url.startswith("ipfs://"):
                    image_url = image_url.replace("ipfs://", "https://ipfs.io/ipfs/")
            except Exception:
                image_url = url_for('static', filename='images/dummy.png')

            try:
                owner = nft_contract.functions.ownerOf(token_id).call()
            except Exception:
                owner = "Unknown"

            results.append({
                "contract_address": nft_address,
                "token_id": token_id,
                "price": w3.from_wei(price_wei, 'ether'),  # in MON
                "symbol": symbol,
                "image_url": image_url,
                "owner": owner
            })
        return render_template('marketplace.html', nfts=results, current_wallet_address=session.get('wallet_address'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
