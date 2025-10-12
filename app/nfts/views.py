import base64
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

        rpc_url = current_app.config.get('MONAD_RPC_URL')
        marketplace_address = Web3.to_checksum_address(
            current_app.config.get('NFT_MARKETPLACE_CONTRACT_ADDRESS')
        )
        with open('/home/byte/Desktop/minty monad/app/static/contract-abi/NFTMarketplace.abi.json') as f:
            marketplace_abi = json.load(f)

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        marketplace_contract = w3.eth.contract(address=marketplace_address, abi=marketplace_abi)
        listed_nfts, listed_token_ids = marketplace_contract.functions.getAllListedNFTs().call()

        listed_set = set(
            (addr.lower(), tid)
            for addr, tid in zip(listed_nfts, listed_token_ids)
        )

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
        with open('/home/byte/Desktop/minty monad/app/static/contract-abi/NFTMarketplace.abi.json') as f:
            marketplace_abi = json.load(f)

        erc721_abi = [
            {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "tokenId", "type": "uint256"}], "name": "tokenURI", "outputs": [{"name": "", "type": "string"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "tokenId", "type": "uint256"}], "name": "ownerOf", "outputs": [{"name": "", "type": "address"}], "type": "function"}
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
                if token_uri.startswith("data:"):
                    base64_data = token_uri.split(",", 1)[1]
                    decoded_json = base64.b64decode(base64_data).decode("utf-8")
                    metadata = json.loads(decoded_json)
                else:
                    metadata = requests.get(token_uri).json()

                image_url = metadata.get("image", url_for('static', filename='images/dummy.png'))
                if image_url.startswith("ipfs://"):
                    image_url = image_url.replace("ipfs://", "https://ipfs.io/ipfs/")
            except Exception as e:
                print(f"Error fetching metadata for token {token_id}:", e)
                image_url = url_for('static', filename='images/dummy.png')

            try:
                owner = nft_contract.functions.ownerOf(token_id).call()
            except Exception:
                owner = "Unknown"

            results.append({
                "contract_address": nft_address,
                "token_id": token_id,
                "price": w3.from_wei(price_wei, 'ether'),  
                "symbol": symbol,
                "image_url": image_url,
                "owner": owner
            })

        return render_template('marketplace.html', nfts=results, current_wallet_address=session.get('wallet_address'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@nfts.route('/view-proposals/<contract_address>/<token_id>')
def view_proposals(contract_address, token_id):
    rpc_url = current_app.config.get('MONAD_RPC_URL')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    marketplace_address = Web3.to_checksum_address(
        current_app.config.get('NFT_MARKETPLACE_CONTRACT_ADDRESS')
    )

    with open('/home/byte/Desktop/minty monad/app/static/contract-abi/NFTMarketplace.abi.json') as f:
        marketplace_abi = json.load(f)

    contract_address = Web3.to_checksum_address(unquote(contract_address))
    token_id = int(unquote(token_id))

    contract = w3.eth.contract(address=marketplace_address, abi=marketplace_abi)
    proposers, prices = contract.functions.getProposalsForNFT(contract_address, token_id).call()

    proposals = []
    for proposer, price in zip(proposers, prices):
        proposals.append({
            "proposer": proposer,
            "price": Web3.from_wei(price, "ether")
        })

    erc721_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_tokenId", "type": "uint256"}],
            "name": "ownerOf",
            "outputs": [{"name": "", "type": "address"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
    nft_contract = w3.eth.contract(address=contract_address, abi=erc721_abi)
    nft_owner_address = nft_contract.functions.ownerOf(token_id).call()

    return render_template(
        'view-proposals.html',
        proposals=proposals,
        contract_address=contract_address,
        token_id=token_id,
        current_wallet_address=session.get('wallet_address'),
        nft_owner_address=nft_owner_address
    )


@nfts.route('/make_offer/<contract_address>/<token_id>')
def make_offer(contract_address, token_id):
    contract_address = unquote(contract_address)
    token_id = unquote(token_id)
    return render_template('makeOffer.html', contract_address=contract_address, token_id=token_id)