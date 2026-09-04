# MintyMonad

MintyMonad is a Flask web application and Vyper smart contract for listing, buying, and making offers on ERC-721 NFTs on Monad Testnet. Wallet authentication uses a server-issued nonce and an EIP-191 signature; transaction execution remains in the user's wallet.

## Scope

- ERC-721 listing and unlisting
- Native MON purchases and offers
- Proposal acceptance, cancellation, and refunds
- Wallet-based authentication
- Monad network and contract metadata APIs

## Architecture

The Flask application serves Jinja templates and static JavaScript. The backend reads marketplace state from the Monad RPC and NFT ownership/metadata from Alchemy and token URIs. The browser wallet signs authentication messages and submits marketplace transactions directly to the contract. SQLite stores the wallet identity used by the web session; blockchain state remains authoritative for NFTs, listings, and offers.

## Requirements

- Python 3.11 recommended
- `uv`
- A browser wallet such as MetaMask
- Monad Testnet RPC access
- An Alchemy NFT API key
- A deployed `NFTMarketplace` contract

## Configuration

Create `.env` locally. Never commit it.

```dotenv
SECRET_KEY=replace-with-a-random-value
ALCHEMY_API_KEY=
NFT_MARKETPLACE_CONTRACT_ADDRESS=
MONAD_RPC_URL=https://testnet-rpc.monad.xyz
MONAD_CHAIN_ID=10143
MONAD_CHAIN_NAME=Monad Testnet
MONAD_NATIVE_NAME=Monad
MONAD_NATIVE_SYMBOL=MON
MONAD_NATIVE_DECIMALS=18
MONAD_EXPLORER_URL=https://testnet.monadexplorer.com/
MONAD_BLOCK_GAS_LIMIT=150000000
```

Windows PowerShell users can create `.env` from `.env.example` in an editor, or use `Copy-Item .env.example .env` before filling in local values.

Deployment-only scripts additionally require `PRIVATE_KEY` and `ACCOUNT_ADDRESS`. Keep these out of source control and run those scripts only against an intended network.

Production requires `SECRET_KEY`, `DATABASE_URL`, `MONAD_RPC_URL`, `ALCHEMY_API_KEY`, and `NFT_MARKETPLACE_CONTRACT_ADDRESS`. The container entrypoint is `wsgi:app` under Gunicorn.

## Run locally

```bash
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe create_db.py
.venv/Scripts/python.exe manage.py
```

Open http://127.0.0.1:5050.

## Container run

```bash
docker compose up --build -d
curl http://127.0.0.1:5050/healthz
curl http://127.0.0.1:5050/readyz
```

See `OPERATIONS.md` for shutdown and rollback guidance.

The container entrypoint applies committed migrations before starting Gunicorn. The mounted `minty-data` volume persists the SQLite demo database; use a managed database for production traffic.

## Verification

```bash
uv run --python 3.11 --with Flask==3.1.1 --with Flask-SQLAlchemy==3.1.1 --with web3==7.13.0 --with python-dotenv==1.1.1 --with eth-account==0.13.7 pytest -q
python -m compileall -q app config.py create_db.py deploy.py manage.py withdrawfee.py
uvx --python 3.11 --from vyper==0.4.3 vyper contracts/NFTMarketplace.vy
```

## API smoke checks

```bash
curl -s http://127.0.0.1:5050/api/network_config
curl -s http://127.0.0.1:5050/api/marketplace_abi
curl -s http://127.0.0.1:5050/api/marketplace_contract_address
```

## Security and limitations

This is a testnet portfolio project, not a production financial application. The contract is not independently audited and has no upgrade mechanism. The backend does not custody funds or submit marketplace transactions. RPC and metadata providers are external dependencies. Production hardening still required includes rate limiting, CSRF protection for backend state changes, structured monitoring, database migrations, a production server configuration, and a formal smart-contract audit.

## License

MIT. See `LICENSE`.
