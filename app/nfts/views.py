import base64
import json
import os
from flask import jsonify, render_template, current_app, request, session, url_for
from . import nfts
from urllib.parse import unquote
import requests
from web3 import Web3


def _abi_path() -> str:
    return os.path.join(current_app.root_path, 'static', 'contract-abi', 'NFTMarketplace.abi.json')


def _get_w3() -> Web3:
    rpc_url = current_app.config.get('MONAD_RPC_URL')
    return Web3(Web3.HTTPProvider(rpc_url))


def _get_marketplace_contract(w3: Web3 = None):
    w3 = w3 or _get_w3()
    marketplace_address = Web3.to_checksum_address(
        current_app.config.get('NFT_MARKETPLACE_CONTRACT_ADDRESS')
    )
    with open(_abi_path()) as f:
        marketplace_abi = json.load(f)
    return w3.eth.contract(address=marketplace_address, abi=marketplace_abi)


def _erc721_abi():
    return [
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [{"name": "tokenId", "type": "uint256"}],
            "name": "tokenURI",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [{"name": "tokenId", "type": "uint256"}],
            "name": "ownerOf",
            "outputs": [{"name": "", "type": "address"}],
            "type": "function",
        },
    ]


def _normalize_ipfs(url: str) -> str:
    if not isinstance(url, str):
        return url
    if url.startswith("ipfs://"):
        return url.replace("ipfs://", "https://ipfs.io/ipfs/")
    return url


def _load_token_metadata(token_uri: str) -> dict:
    token_uri = _normalize_ipfs(token_uri)
    if not token_uri:
        return {}
    try:
        if token_uri.startswith("data:"):
            base64_data = token_uri.split(",", 1)[1]
            decoded_json = base64.b64decode(base64_data).decode("utf-8")
            return json.loads(decoded_json)
        resp = requests.get(token_uri, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        current_app.logger.exception("Failed to load token metadata from %s", token_uri)
        return {}


def _image_from_metadata(metadata: dict) -> str:
    image_url = metadata.get("image") if isinstance(metadata, dict) else None
    image_url = _normalize_ipfs(image_url) if image_url else None
    return image_url or url_for('static', filename='images/dummy.png')


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

        w3 = _get_w3()
        marketplace_contract = _get_marketplace_contract(w3)
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
        current_app.logger.exception("Failed to fetch owned NFTs from Alchemy")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        current_app.logger.exception("Unexpected error in my_nfts")
        return jsonify({"error": str(e)}), 500


@nfts.route('/marketplace-data', methods=['GET'])
def marketplace_data():
    try:
        w3 = _get_w3()
        marketplace_contract = _get_marketplace_contract(w3)
        erc721_abi = _erc721_abi()
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
                metadata = _load_token_metadata(token_uri)
                image_url = _image_from_metadata(metadata)
            except Exception:
                current_app.logger.exception("Error fetching metadata for token %s", token_id)
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
        current_app.logger.exception("Unexpected error in marketplace_data")
        return jsonify({"error": str(e)}), 500

@nfts.route('/view-proposals/<contract_address>/<token_id>')
def view_proposals(contract_address, token_id):
    w3 = _get_w3()
    marketplace_contract = _get_marketplace_contract(w3)

    contract_address = Web3.to_checksum_address(unquote(contract_address))
    token_id = int(unquote(token_id))
    proposers, prices = marketplace_contract.functions.getProposalsForNFT(contract_address, token_id).call()

    proposals = []
    for proposer, price in zip(proposers, prices):
        proposals.append({
            "proposer": proposer,
            "price": Web3.from_wei(price, "ether")
        })

    erc721_owner_abi = [a for a in _erc721_abi() if a["name"] == "ownerOf"]
    nft_contract = w3.eth.contract(address=contract_address, abi=erc721_owner_abi)
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