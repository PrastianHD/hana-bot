import json
import requests
from web3 import Web3
from colorama import Fore, Style
import os
import time

# Configuration
RPC_URL = "https://mainnet.base.org"
CONTRACT_ADDRESS = "0xC5bf05cD32a14BFfb705Fb37a9d218895187376c"
AMOUNT_ETH = 0.00000001  # ETH to deposit
GRAPHQL_URL = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
api_key = "AIzaSyDipzN0VRfTPnMGhQ5PSzO27Cxm3DohJGY"  # Ganti dengan API Key Anda

# Load account details from account.json
with open("account.json", "r") as file:
    accounts = json.load(file)

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Smart contract ABI for deposit function
contract_abi = '''
[
    {
        "inputs": [],
        "name": "depositETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]
'''
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=json.loads(contract_abi))
amount_wei = web3.to_wei(AMOUNT_ETH, 'ether')

# Create history folder if it does not exist
os.makedirs("history", exist_ok=True)

def refresh_access_token(refresh_token):
    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })
    response = requests.post(url, headers=headers, data=body)
    if response.status_code != 200:
        error_response = response.json()
        raise Exception(f"Failed to refresh access token: {error_response['error']}")
    return response.json()["access_token"]

def post_tx_hash(bearer_token, tx_hash, proxy_url):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    payload = {
        "query": "mutation SyncEthereumTx($chainId: Int!, $txHash: String!) { syncEthereumTx(chainId: $chainId, txHash: $txHash) }",
        "variables": {
            "chainId": 8453,
            "txHash": tx_hash
        },
        "operationName": "SyncEthereumTx"
    }
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }

    try:
        response = requests.post(GRAPHQL_URL, json=payload, headers=headers, proxies=proxies)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
        else:
            print(f"GraphQL response for txHash {tx_hash}: {response.json()}")
    except Exception as e:
        print(f"Error posting txHash {tx_hash}: {e}")

def send_transaction(account):
    private_key = account["privateKey"]
    from_address = web3.eth.account.from_key(private_key).address
    short_from_address = from_address[:4] + "..." + from_address[-4:]
    nonce = web3.eth.get_transaction_count(from_address)
    base_fee = web3.eth.get_block('latest').baseFeePerGas
    max_priority_fee = web3.to_wei(0.0012, 'gwei')
    max_fee_per_gas = base_fee + max_priority_fee

    transaction = contract.functions.depositETH().build_transaction({
        'from': from_address,
        'value': amount_wei,
        'gas': 54405,
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee,
        'nonce': nonce,
        'type': '0x2'
    })
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)

    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(Fore.GREEN + f"Transaction {nonce} sent from {short_from_address} with hash: {tx_hash.hex()}")
        
        # Wait for confirmation
        web3.eth.wait_for_transaction_receipt(tx_hash)
        time.sleep(1)
        
        # Save tx hash to file
        tx_hash_file_path = f"history/{from_address}.txt"
        with open(tx_hash_file_path, "a") as tx_file:
            tx_file.write(tx_hash.hex() + "\n")
        
        return tx_hash.hex()
    
    except Exception as e:
        print(f"Error sending transaction for {short_from_address}: {e}")
        return None

# Prompt user for the number of transactions
num_transactions = int(input(Fore.GREEN + "Enter the number of transactions to be executed per account: " + Style.RESET_ALL))

# Execute transactions in a round-robin pattern
transaction_count = {account["privateKey"]: 0 for account in accounts}  # Track transaction counts per account

for i in range(num_transactions):
    for account in accounts:
        # Refresh access token every 50 transactions
        if transaction_count[account["privateKey"]] % 50 == 0:
            refresh_token = account["refresh_token"]
            proxy_url = account["proxy"]
            bearer_token = refresh_access_token(refresh_token)
        
        # Send transaction
        tx_hash = send_transaction(account)
        
        if tx_hash:
            # Post tx_hash to GraphQL
            post_tx_hash(bearer_token, tx_hash, proxy_url)
        
        # Increment transaction count
        transaction_count[account["privateKey"]] += 1
