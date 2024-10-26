import json
import requests
from web3 import Web3
from colorama import Fore, Style
import time

# Configuration
RPC_URL = "https://mainnet.base.org"
CONTRACT_ADDRESS = "0xC5bf05cD32a14BFfb705Fb37a9d218895187376c"
AMOUNT_ETH = 0.0000001  # ETH to deposit
GRAPHQL_URL = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"

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

# Send transaction and post tx hash
def send_transaction_and_post(account):
    private_key = account["privateKey"]
    bearer_token = account["bearer"]
    proxy = account["proxy"]

    # Derive wallet address from private key
    from_address = web3.eth.account.from_key(private_key).address
    short_from_address = from_address[:4] + "..." + from_address[-4:]
    
    # Set up proxies
    proxies = {
        "http": proxy,
        "https": proxy
    }

    # Get nonce for the transaction
    nonce = web3.eth.get_transaction_count(from_address)

    # Retrieve the current Base Fee from the latest block
    base_fee = web3.eth.get_block('latest').baseFeePerGas
    max_priority_fee = web3.to_wei(0.0012, 'gwei')  # Set your desired priority fee
    max_fee_per_gas = base_fee + max_priority_fee  # Calculate max fee per gas based on base fee

    transaction = contract.functions.depositETH().build_transaction({
        'from': from_address,
        'value': amount_wei,
        'gas': 54405,  # Estimated gas limit
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee,
        'nonce': nonce,
        'type': '0x2'  # Transaction Type 2 (EIP-1559)
    })

    # Sign transaction
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)

    # Send transaction
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        web3.eth.wait_for_transaction_receipt(tx_hash)
        print(Fore.GREEN + f"Transaction {nonce} sent from {short_from_address} with hash: {tx_hash.hex()}")
        time.sleep(2)

        # Post transaction hash to GraphQL endpoint
        post_tx_hash(bearer_token, tx_hash.hex(), proxies)
    except Exception as e:
        print(f"Error sending transaction for {short_from_address}: {e}")

# Post transaction hash to the GraphQL endpoint
def post_tx_hash(bearer_token, tx_hash, proxies):
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {bearer_token}"  # Ensure "Bearer " is included
    }
    payload = {
        "query": "mutation SyncEthereumTx($chainId: Int!, $txHash: String!) { \nsyncEthereumTx(chainId: $chainId, txHash: $txHash)\n }",
        "variables": {
            "chainId": 8453,
            "txHash": tx_hash
        },
        "operationName": "SyncEthereumTx"
    }

    try:
        response = requests.post(GRAPHQL_URL, json=payload, headers=headers, proxies=proxies)
          # Check for errors in the response
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
        else:
            print(f"GraphQL response : {response.json()}")
    except Exception as e:
        print(f"Error posting txHash {tx_hash}: {e}")

# Prompt user for the number of transactions
num_transactions = int(input(Fore.GREEN + "Enter the number of transactions to be executed per account: " + Style.RESET_ALL))

# Execute transactions in a round-robin pattern
for i in range(num_transactions):
    for account in accounts:
        send_transaction_and_post(account)
