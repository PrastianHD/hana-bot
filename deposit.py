import json
import requests
from web3 import Web3
import os
import time
from headers import deposit_headers  # Import the headers module

# Configuration
RPC_URL = "https://mainnet.base.org"
CONTRACT_ADDRESS = "0xC5bf05cD32a14BFfb705Fb37a9d218895187376c"
AMOUNT_ETH = 0.00000001  # ETH to deposit
GRAPHQL_URL = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
api_key = "AIzaSyDipzN0VRfTPnMGhQ5PSzO27Cxm3DohJGY"  # Replace with your API key

# Load account details
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
    body = json.dumps({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=body)
    
    if response.status_code != 200:
        error_response = response.json()
        raise Exception(f"Failed to refresh access token: {error_response['error']}")
    
    return response.json()["access_token"]

def post_tx_hash(bearer_token, tx_hash, proxy_url):
    headers = deposit_headers(bearer_token)  # Get headers from headers.py
    # Pastikan tx_hash selalu memiliki prefix "0x"
    tx_hash_prefixed = f"0x{tx_hash.lstrip('0x')}"

    payload = {
        "query": "mutation SyncEthereumTx($chainId: Int!, $txHash: String!) { syncEthereumTx(chainId: $chainId, txHash: $txHash) }",
        "variables": {
            "chainId": 8453,
            "txHash": tx_hash_prefixed  # Gunakan hash dengan "0x"
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
            print(f"GraphQL response for txHash 0x{tx_hash}: {response.json()}")
    except Exception as e:
        print(f"Error posting txHash {tx_hash}: {e}")

def send_transaction(account):
    private_key = account["privateKey"]
    from_address = web3.eth.account.from_key(private_key).address
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
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"Transaction {nonce} sent from {from_address[:4]}...{from_address[-4:]} with hash: 0x{tx_hash.hex()}")
        
        # Wait for confirmation
        web3.eth.wait_for_transaction_receipt(tx_hash)
        time.sleep(5)
        
        # Save tx hash to file
        with open(f"history/{from_address}.txt", "a") as tx_file:
            tx_file.write("0x" + tx_hash.hex() + "\n")
        
        return tx_hash.hex()
    
    except Exception as e:
        print(f"Error sending transaction for {from_address[:4]}...{from_address[-4:]}: {e}")
        return None

# Prompt user for the number of transactions
num_transactions = int(input("Enter the number of transactions per account: "))

# Execute transactions
transaction_count = {account["privateKey"]: 0 for account in accounts}

for _ in range(num_transactions):
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
