import json
import os
from urllib.parse import unquote
from flask import jsonify, render_template, request, session, url_for, current_app
import os

from app.model import User
from . import api
from app import db

@api.route('/login', methods=['POST'])
def wallet_login():
    """Create or fetch a user by wallet address and start a session."""
    data = request.get_json()
    wallet_address = data.get('wallet_address')

    if not wallet_address:
        return jsonify({'error': 'Wallet address is required'}), 400

    user = User.query.filter_by(wallet_address=wallet_address).first()
    if not user:
        user = User(wallet_address=wallet_address)
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
    session['wallet_address'] = user.wallet_address

    return jsonify({'id': user.id, 'wallet_address': user.wallet_address})

@api.route('/logout', methods=['GET'])
def wallet_logout():
    """Clear session to log out the current user."""
    # Clear the session data
    session.pop('user_id', None)
    session.pop('wallet_address', None)
    
    return jsonify({'message': 'Successfully logged out'})

@api.route('/marketplace_abi', methods=['GET'])
def get_marketplace_abi():
    """Return the marketplace contract ABI for frontend contract interactions."""
    try:
        abi_path = os.path.join(current_app.root_path, 'static', 'contract-abi', 'NFTMarketplace.abi.json')
        with open(abi_path, 'r') as f:
            abi = json.load(f)
        
        return jsonify(abi)
    
    except FileNotFoundError:
        return jsonify({'error': 'ABI file not found'}), 404
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid ABI file format'}), 500
    
    except Exception as e:
        current_app.logger.exception('Unexpected error reading marketplace ABI')
        return jsonify({'error': str(e)}), 500
    

@api.route('/marketplace_contract_address', methods=['GET'])
def get_marketplace_contract_address():
    """Return the deployed marketplace contract address from server config."""
    return jsonify({'contract_address': current_app.config.get('NFT_MARKETPLACE_CONTRACT_ADDRESS')})


@api.route('/network_config', methods=['GET'])
def get_network_config():
    """Return network configuration for the frontend wallet to use when adding/switching chains."""
    # Provide sensible defaults but allow overrides via app config / env
    chain_id_dec = current_app.config.get('MONAD_CHAIN_ID', 10143)
    try:
        chain_id_int = int(chain_id_dec)
    except Exception:
        chain_id_int = 10143

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