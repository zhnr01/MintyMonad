from web3 import Web3
import json
from dotenv import load_dotenv
import os

load_dotenv()

MONAD_RPC = os.environ.get('MONAD_RPC')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')
ACCOUNT_ADDRESS = '0xYourAccountAddressHere'  # Replace with your account address
CONTRACT_ADDRESS = '0x7a5271F3Ca14b7541b3E5d9C80691fa983eC66BF'
MON_TOKEN_ADDRESS = ''

with open("contracts/NFTMarketplace.abi.json") as f:
    MARKETPLACE_ABI = json.load(f)

with open("contracts/MONToken.abi.json") as f:
    TOKEN_ABI = json.load(f)

w3 = Web3(Web3.HTTPProvider(MONAD_RPC))
marketplace = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=MARKETPLACE_ABI)
mon_token = w3.eth.contract(address=Web3.to_checksum_address(MON_TOKEN_ADDRESS), abi=TOKEN_ABI)

balance = mon_token.functions.balanceOf(CONTRACT_ADDRESS).call()
if balance == 0:
    print("Marketplace has no MON tokens.")
    exit()

withdraw_to = Web3.to_checksum_address(ACCOUNT_ADDRESS)
gas_price = w3.eth.gas_price
gas_estimate = marketplace.functions.withdrawFees(withdraw_to).estimate_gas({'from': ACCOUNT_ADDRESS})

transaction = marketplace.functions.withdrawFees(withdraw_to).build_transaction({
    'from': ACCOUNT_ADDRESS,
    'nonce': w3.eth.get_transaction_count(ACCOUNT_ADDRESS),
    'gas': gas_estimate,
    'gasPrice': gas_price
})

signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
print(f"Withdrawing fees... TX hash: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Withdraw successful in block {receipt.blockNumber}")
