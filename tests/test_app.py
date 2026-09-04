import pytest
from eth_account import Account
from eth_account.messages import encode_defunct

from app import create_app, db
from app.nfts.metadata import load_token_metadata, validate_public_metadata_url


@pytest.fixture()
def client():
    app = create_app('testing')
    app.config.update(
        SECRET_KEY='test-secret',
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        NFT_MARKETPLACE_CONTRACT_ADDRESS=None,
        MONAD_RPC_URL='https://example.com',
        ALCHEMY_API_KEY='test-key',
    )
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_health_and_readiness(client):
    assert client.get('/healthz').get_json() == {'status': 'ok'}
    readiness = client.get('/readyz')
    assert readiness.status_code == 200
    assert readiness.get_json() == {'database': 'ok', 'status': 'ready'}


def test_request_id_is_safe_and_propagated(client):
    response = client.get('/healthz', headers={'X-Request-ID': 'trace_123'})
    assert response.headers['X-Request-ID'] == 'trace_123'
    hostile = client.get('/healthz', headers={'X-Request-ID': '<script>'})
    assert hostile.headers['X-Request-ID'] != '<script>'


def test_home_and_network_config_are_available(client):
    home = client.get('/')
    network = client.get('/api/network_config')
    assert home.status_code == 200
    assert network.status_code == 200
    assert network.get_json()['chainId'] == '0x279f'
    assert home.headers['X-Content-Type-Options'] == 'nosniff'


def test_contract_address_fails_safely_when_unconfigured(client):
    response = client.get('/api/marketplace_contract_address')
    assert response.status_code == 503
    assert response.get_json() == {'error': 'Marketplace contract is not configured'}


def test_wallet_login_requires_csrf_and_signature(client):
    account = Account.create()
    assert client.post('/api/login').status_code == 403
    csrf_token = client.get('/api/csrf-token').get_json()['csrf_token']
    headers = {'X-CSRF-Token': csrf_token}
    response = client.post('/api/login', json={'wallet_address': account.address}, headers=headers)
    assert response.status_code == 401


def test_wallet_login_verifies_address_ownership_and_rejects_replay(client):
    account = Account.create()
    other_account = Account.create()
    csrf_token = client.get('/api/csrf-token').get_json()['csrf_token']
    headers = {'X-CSRF-Token': csrf_token}
    nonce = client.post('/api/nonce', json={'wallet_address': account.address}, headers=headers).get_json()['nonce']
    signature = Account.sign_message(encode_defunct(text=nonce), account.key).signature.hex()
    payload = {'wallet_address': other_account.address, 'nonce': nonce, 'signature': signature}
    assert client.post('/api/login', json=payload, headers=headers).status_code == 401
    payload['wallet_address'] = account.address
    assert client.post('/api/login', json=payload, headers=headers).status_code == 200
    assert client.post('/api/login', json=payload, headers=headers).status_code == 401


def test_logout_is_post_only(client):
    assert client.get('/api/logout').status_code == 405
    csrf_token = client.get('/api/csrf-token').get_json()['csrf_token']
    assert client.post('/api/logout', headers={'X-CSRF-Token': csrf_token}).status_code == 200


def test_metadata_rejects_non_public_urls():
    with pytest.raises(ValueError):
        validate_public_metadata_url('http://127.0.0.1:8000/metadata.json')
    assert load_token_metadata('http://127.0.0.1:8000/metadata.json') == {}
    with pytest.raises(ValueError):
        validate_public_metadata_url('https://example.com/metadata.json')


def test_metadata_rejects_oversized_data_uri():
    payload = 'data:application/json;base64,' + ('A' * 1_398_105)
    assert load_token_metadata(payload) == {}
