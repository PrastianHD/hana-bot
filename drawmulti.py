import requests
import json
import time
import logging
from colorama import Fore, Style
from headers import get_draw_headers  # Mengimpor headers dari draw_headers.py

# Konstanta
API_KEY = "AIzaSyDipzN0VRfTPnMGhQ5PSzO27Cxm3DohJGY"
GRAPHQL_URL = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
ACCOUNT_FILE = "account.json"

def refresh_access_token(refresh_token):
    """Memperbarui access token menggunakan refresh token."""
    url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
    
    body = json.dumps({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })

    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, data=body)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error refreshing access token: {e}")
        raise Exception("Failed to refresh access token.")

def print_intro():
    """Menampilkan teks intro."""
    print(Fore.BLUE + Style.BRIGHT + "Auto Draw for HANAFUDA | Multi Account" + Style.RESET_ALL)

def load_accounts():
    """Memuat akun dari file JSON."""
    try:
        with open(ACCOUNT_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"File '{ACCOUNT_FILE}' not found.")
        print(f"File '{ACCOUNT_FILE}' tidak ditemukan.")
        exit()

def execute_draw_actions(headers):
    """Menjalankan aksi menggambar kartu dan menampilkan hasil draw."""
    # Query mendapatkan list Hanafuda
    query_get_hanafuda_list = {
        "query": "query getHanafudaList($groups: [YakuGroup!]) { getYakuListForCurrentUser(groups: $groups) { cardId group } }",
        "variables": {},
        "operationName": "getHanafudaList"
    }
    response_list = requests.post(GRAPHQL_URL, headers=headers, json=query_get_hanafuda_list)
    
    if response_list.status_code == 200:
        hanafuda_list = response_list.json().get('data', {}).get('getYakuListForCurrentUser', [])
        print(Fore.YELLOW + Style.BRIGHT + "=== Hanafuda List ===" + Style.RESET_ALL)
        for card in hanafuda_list:
            print(f"Card ID: {card.get('cardId', 'N/A')} | Group: {card.get('group', 'N/A')}")
        print("=" * 30)

    # Mutasi eksekusi tindakan Garden Reward
    mutation_execute_garden_reward = {
        "query": "mutation executeGardenRewardAction($limit: Int!) { executeGardenRewardAction(limit: $limit) { data { cardId group } isNew } }",
        "variables": {"limit": 10},
        "operationName": "executeGardenRewardAction"
    }
    response_garden_reward = requests.post(GRAPHQL_URL, headers=headers, json=mutation_execute_garden_reward)

    if response_garden_reward.status_code == 200:
        garden_reward_data = response_garden_reward.json()
        
        # Pastikan response memiliki data yang benar
        reward_list = garden_reward_data.get('data', {}).get('executeGardenRewardAction', [])
        if reward_list:
            print(Fore.GREEN + Style.BRIGHT + f"\n=== Draw Result ===" + Style.RESET_ALL)
            print("Card ID   | Group   | Is New")
            print("-" * 30)

            for item in reward_list:
                card_id = item.get('data', {}).get('cardId', "N/A")
                group = item.get('data', {}).get('group', "N/A")
                is_new = item.get('isNew', False)
                print(f"{card_id:<8} | {group:<7} | {is_new}")
                logging.info(f"Draw: Card ID: {card_id}, Group: {group}, Is New: {is_new}")
        else:
            print(Fore.RED + "No new draw results found!" + Style.RESET_ALL)
            logging.warning("No draw results received from API.")
    else:
        print(Fore.RED + "Failed to execute draw action!" + Style.RESET_ALL)
        logging.error(f"Error fetching draw results: {response_garden_reward.text}")


def get_garden_status(headers):
    """Mendapatkan status taman pengguna saat ini."""
    query_get_garden = {
        "query": "query GetGardenForCurrentUser { getGardenForCurrentUser { id inviteCode gardenDepositCount gardenStatus { id activeEpoch growActionCount gardenRewardActionCount } gardenMilestoneRewardInfo { id gardenDepositCountWhenLastCalculated lastAcquiredAt createdAt } gardenMembers { id sub name iconPath depositCount } } }",
        "operationName": "GetGardenForCurrentUser"
    }
    response_garden = requests.post(GRAPHQL_URL, headers=headers, json=query_get_garden)
    if response_garden.status_code == 200:
        return response_garden.json()
    return {}

def main():
    """Fungsi utama untuk menjalankan program."""
    print_intro()
    accounts = load_accounts()

    # Input jumlah iterasi
    try:
        num_iterations = int(input(Fore.BLUE + Style.BRIGHT + "Masukkan Jumlah Draw: " + Style.RESET_ALL))
        if num_iterations <= 0:
            raise ValueError("The number of iterations must be a positive integer.")
    except ValueError as e:
        logging.error(f"Invalid input: {e}")
        print(Fore.RED + "Input tidak valid." + Style.RESET_ALL)
        exit()

    while True:
        for account in accounts:
            refresh_token = account.get('refresh_token')
            proxy = account.get('proxy')

            try:
                # Setup session dengan proxy jika tersedia
                session = requests.Session()
                if proxy:
                    session.proxies = {"http": proxy, "https": proxy}
                    logging.info(f"Connected to proxy: {proxy}")

                # Perbarui token akses
                token_data = refresh_access_token(refresh_token)
                access_token = token_data["access_token"]

                # Ambil headers dari draw_headers.py
                headers = get_draw_headers(access_token)

                # Eksekusi aksi draw
                for _ in range(num_iterations):
                    print(Fore.CYAN + Style.BRIGHT + f"\nExecuting draw for account: {account.get('privateKey', 'Unknown')[:6]}..." + Style.RESET_ALL)
                    execute_draw_actions(headers)

                    # Mendapatkan data taman pengguna
                    get_garden_status(headers)

                    print(Fore.BLUE + Style.BRIGHT + f"\n=== Delay 1 minutes ===" + Style.RESET_ALL)
                    time.sleep(60)
                    
                      # Delay sebelum iterasi berikutnya

            except Exception as e:
                logging.error(f"Error processing account {account.get('privateKey', 'Unknown')}: {e}")

        # Delay sebelum batch berikutnya
        for remaining in range(60, 0, -1):
            print(f"Tunggu {remaining} detik sebelum batch berikutnya...", end="\r")
            time.sleep(1)

if __name__ == "__main__":
    main()
