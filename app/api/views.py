import json
import os
import secrets
import time
from functools import wraps
from flask import current_app, jsonify, request, session
from web3 import Web3
from eth_account.messages import encode_defunct

from app.model import User
from . import api
from app import db


def csrf_protected(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = request.headers.get('X-CSRF-Token', '')
        if not token or not session.get('csrf_token') or not secrets.compare_digest(token, session['csrf_token']):
            return jsonify({'error': 'CSRF validation failed'}), 403
        return view(*args, **kwargs)
    return wrapped

@api.route('/login', methods=['POST'])
@csrf_protected
def wallet_login():

    data = request.get_json(silent=True) or {}
    wallet_address = data.get('wallet_address', '')
    signature = data.get('signature', '')
    nonce = data.get('nonce', '')

    if not isinstance(wallet_address, str) or not Web3.is_address(wallet_address):
        return jsonify({'error': 'Wallet address is required'}), 400
    wallet_address = Web3.to_checksum_address(wallet_address)
    expected_nonce = session.get('wallet_nonce')
    nonce_wallet = session.get('wallet_nonce_wallet')
    nonce_issued_at = session.get('wallet_nonce_issued_at', 0)
    if (not isinstance(signature, str) or not isinstance(nonce, str) or nonce != expected_nonce
            or nonce_wallet != wallet_address or time.time() - nonce_issued_at > 300):
        return jsonify({'error': 'Wallet verification is required'}), 401
    try:
        recovered_address = Web3.to_checksum_address(
            Web3().eth.account.recover_message(encode_defunct(text=nonce), signature=signature)
        )
    except Exception:
        return jsonify({'error': 'Invalid wallet signature'}), 401
    if recovered_address != wallet_address:
        return jsonify({'error': 'Wallet signature does not match address'}), 401
    csrf_token = session.get('csrf_token')
    session.clear()
    session['csrf_token'] = csrf_token
    session.pop('wallet_nonce_wallet', None)
    session.pop('wallet_nonce_issued_at', None)

    user = User.query.filter_by(wallet_address=wallet_address).first()
    if not user:
        user = User(wallet_address=wallet_address)
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
    session['wallet_address'] = user.wallet_address

    return jsonify({'id': user.id, 'wallet_address': user.wallet_address})


@api.route('/nonce', methods=['POST'])
@csrf_protected
def wallet_nonce():
    data = request.get_json(silent=True) or {}
    wallet_address = data.get('wallet_address', '')
    if not isinstance(wallet_address, str) or not Web3.is_address(wallet_address):
        return jsonify({'error': 'Wallet address is required'}), 400
    nonce = secrets.token_urlsafe(32)
    session['wallet_nonce'] = nonce
    session['wallet_nonce_wallet'] = Web3.to_checksum_address(wallet_address)
    session['wallet_nonce_issued_at'] = time.time()
    return jsonify({'nonce': nonce})


@api.route('/csrf-token', methods=['GET'])
def csrf_token():
    token = session.get('csrf_token') or secrets.token_urlsafe(32)
    session['csrf_token'] = token
    return jsonify({'csrf_token': token})

@api.route('/logout', methods=['POST'])
@csrf_protected
def wallet_logout():

    session.clear()
    
    return jsonify({'message': 'Successfully logged out'})

@api.route('/marketplace_abi', methods=['GET'])
def get_marketplace_abi():

    try:
        abi_path = os.path.join(current_app.root_path, 'static', 'contract-abi', 'NFTMarketplace.abi.json')
        with open(abi_path, 'r') as f:
            abi = json.load(f)
        
        return jsonify(abi)
    
    except FileNotFoundError:
        return jsonify({'error': 'ABI file not found'}), 404
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid ABI file format'}), 500
    
    except Exception:
        current_app.logger.exception('Unexpected error reading marketplace ABI')
        return jsonify({'error': 'Unable to load marketplace ABI'}), 500
    

@api.route('/marketplace_contract_address', methods=['GET'])
def get_marketplace_contract_address():

    address = current_app.config.get('NFT_MARKETPLACE_CONTRACT_ADDRESS')
    if not address or not Web3.is_address(address):
        return jsonify({'error': 'Marketplace contract is not configured'}), 503
    return jsonify({'contract_address': Web3.to_checksum_address(address)})


@api.route('/network_config', methods=['GET'])
def get_network_config():

    chain_id_dec = current_app.config.get('MONAD_CHAIN_ID', 10143)
    chain_id_int = int(chain_id_dec)

    rpc_url = current_app.config.get('MONAD_RPC_URL') or current_app.config.get('MONAD_RPC') or ''
    network = {
        'chainId': hex(chain_id_int),
        'chainName': current_app.config.get('MONAD_CHAIN_NAME', 'Monad Testnet'),
        'nativeCurrency': {
            'name': current_app.config.get('MONAD_NATIVE_NAME', 'Monad'),
            'symbol': current_app.config.get('MONAD_NATIVE_SYMBOL', 'MON'),
            'decimals': int(current_app.config.get('MONAD_NATIVE_DECIMALS', 18)),
        },
        'rpcUrls': [rpc_url] if rpc_url else [],
        'blockExplorerUrls': [current_app.config.get('MONAD_EXPLORER_URL', 'https://testnet.monadexplorer.com/')],
        'blockGasLimit': int(current_app.config.get('MONAD_BLOCK_GAS_LIMIT', 150000000)),
    }

    return jsonify(network)