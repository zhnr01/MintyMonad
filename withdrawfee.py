from web3 import Web3
import json
from dotenv import load_dotenv
import os

load_dotenv()

MONAD_RPC = os.environ.get('MONAD_RPC')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')
ACCOUNT_ADDRESS = '0xa8F4f8e7c8981B4424cB2640F3779B3a8068994b'  # Your wallet (must be contract owner)
CONTRACT_ADDRESS = '0x02F54869f96E809828d68c3D6D88482d00Aa08ae'  # Marketplace contract

# Load ABI
with open("contracts/NFTMarketplace.abi.json") as f:
    MARKETPLACE_ABI = json.load(f)

# Connect Web3
w3 = Web3(Web3.HTTPProvider(MONAD_RPC))
marketplace = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=MARKETPLACE_ABI)

# Check how much fees are available
collected_fees = marketplace.functions.collected_fees().call()
if collected_fees == 0:
    print("Marketplace has no fees to withdraw.")
    exit()

# Withdraw fees
withdraw_to = Web3.to_checksum_address(ACCOUNT_ADDRESS)
gas_price = w3.eth.gas_price

gas_estimate = marketplace.functions.withdrawFees(withdraw_to).estimate_gas({
    'from': ACCOUNT_ADDRESS
})

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
