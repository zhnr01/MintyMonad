import json
from pathlib import Path

from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

RPC_URL = os.environ.get('MONAD_RPC_URL') or os.environ.get('MONAD_RPC')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')
ACCOUNT_ADDRESS = os.environ.get('ACCOUNT_ADDRESS')

if not RPC_URL or not PRIVATE_KEY or not ACCOUNT_ADDRESS:
    raise SystemExit('MONAD_RPC_URL, PRIVATE_KEY, and ACCOUNT_ADDRESS are required')

abi_path = Path(__file__).parent / 'contracts' / 'NFTMarketplace.abi.json'
bytecode_path = Path(__file__).parent / 'contracts' / 'NFTMarketplace.bytecode'
with abi_path.open(encoding='utf-8') as file:
    abi = json.load(file)
with bytecode_path.open(encoding='utf-8') as file:
    bytecode = file.read().strip()

web3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 15}))
if not web3.is_connected():
    raise SystemExit('Unable to connect to configured network')

account = Web3.to_checksum_address(ACCOUNT_ADDRESS)
contract = web3.eth.contract(abi=abi, bytecode=bytecode)
transaction = contract.constructor().build_transaction({
    'from': account,
    'nonce': web3.eth.get_transaction_count(account),
    'gas': contract.constructor().estimate_gas({'from': account}),
    'gasPrice': web3.eth.gas_price,
})
signed = web3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
print(receipt.contractAddress)
