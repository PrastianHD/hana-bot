import json
import requests
from web3 import Web3

def refresh_access_token(refresh_token):
    api_key = "AIzaSyDipzN0VRfTPnMGhQ5PSzO27Cxm3DohJGY"  # Ganti dengan API Key Anda
    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"

    headers = {
        "Content-Type": "application/json",
    }

    body = json.dumps({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })

    response = requests.post(url, headers=headers, data=body)

    if response.status_code != 200:
        error_response = response.json()
        raise Exception(f"Failed to refresh access token: {error_response['error']}")

    return response.json()

# Load data from account.json
with open("account.json", "r") as account_file:
    accounts = json.load(account_file)

# Initialize Web3
web3 = Web3()  # Ensure you set up the Web3 provider appropriately

# Define GraphQL URL
GRAPHQL_URL = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"

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

# Iterate over each account
for account in accounts:
    private_key = account.get("privateKey")
    refresh_token = account.get("refresh_token")
    proxy = account.get("proxy")
    from_address = web3.eth.account.from_key(private_key).address

    # Load transaction hashes from the corresponding history file
    tx_hash_file_path = f"history/{from_address}.txt"
    
    try:
        with open(tx_hash_file_path, "r") as tx_file:
            tx_hashes = [line.strip() for line in tx_file if line.strip()]
    except FileNotFoundError:
        print(f"Transaction hash file not found for address: {from_address}")
        continue

    # Initialize bearer token
    token_data = refresh_access_token(refresh_token)
    bearer_token = token_data["access_token"]

    # Iterate through transaction hashes
    for i, tx_hash in enumerate(tx_hashes):
        # Refresh access token every 50 transactions
        if i > 0 and i % 50 == 0:
            token_data = refresh_access_token(refresh_token)
            bearer_token = token_data["access_token"]

        post_tx_hash(bearer_token, tx_hash, proxy)
