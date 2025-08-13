import json
import os
from urllib.parse import unquote
from flask import jsonify, render_template, request, session, url_for

from app.model import User
from . import api
from app import db

@api.route('/login', methods=['POST'])
def wallet_login():
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
    # Clear the session data
    session.pop('user_id', None)
    session.pop('wallet_address', None)
    
    return jsonify({'message': 'Successfully logged out'})

@api.route('/marketplace_abi', methods=['GET'])
def get_marketplace_abi():
    try:
        ABI_PATH = '/home/byte/Desktop/minty monad/app/static/NFTMarketplace.abi.json'
        with open(ABI_PATH, 'r') as f:
            abi = json.load(f)
        
        return jsonify(abi)
    
    except FileNotFoundError:
        return jsonify({'error': 'ABI file not found'}), 404
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid ABI file format'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500