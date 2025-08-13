from web3 import Web3
import json
from dotenv import load_dotenv
import os

load_dotenv()

MONAD_RPC = os.environ.get('MONAD_RPC')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')
ACCOUNT_ADDRESS = os.environ.get('ACCOUNT_ADDRESS')

with open("contracts/NFTMarketplace.abi.json") as f:
    ABI = json.load(f)

with open("contracts/NFTMarketplace.bytecode") as f:
    BYTECODE = f.read().strip()

w3 = Web3(Web3.HTTPProvider(MONAD_RPC))
assert w3.is_connected(), "Failed to connect to network"
Marketplace = w3.eth.contract(abi=ABI, bytecode=BYTECODE)

gas_price = w3.eth.gas_price
gas_estimate = Marketplace.constructor().estimate_gas({'from': ACCOUNT_ADDRESS})

print(f"Current gas price: {w3.from_wei(gas_price, 'gwei')} gwei")
print(f"Estimated gas: {gas_estimate}")

transaction = Marketplace.constructor().build_transaction({
    'from': ACCOUNT_ADDRESS,
    'nonce': w3.eth.get_transaction_count(ACCOUNT_ADDRESS),
    'gas': gas_estimate,
    'gasPrice': gas_price
})

signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)

tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
print(f"Deploying contract... TX hash: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Contract deployed at: {receipt.contractAddress}")
