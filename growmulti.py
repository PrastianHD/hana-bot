import requests
import json
import time
import logging
from colorama import Fore, Style
from headers import get_grow_headers  # Import headers dari grow_headers.py

# Konfigurasi logging
logging.basicConfig(filename='hana_auto_grow.log', level=logging.INFO)

# Konstanta
GRAPHQL_URL = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
ACCOUNT_FILE = "account.json"
CYCLE_DELAY = 60 * 60  # 40 menit dalam detik

def refresh_access_token(refresh_token):
    """Memperbarui access token menggunakan refresh token."""
    API_KEY = "AIzaSyDipzN0VRfTPnMGhQ5PSzO27Cxm3DohJGY"
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
    print(Fore.CYAN + Style.BRIGHT + "Auto Grow for HANA Network Multi Account" + Style.RESET_ALL)

def load_accounts():
    """Memuat akun dari file JSON."""
    try:
        with open(ACCOUNT_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"File '{ACCOUNT_FILE}' not found.")
        print(Fore.RED + Style.BRIGHT + f"File '{ACCOUNT_FILE}' tidak ditemukan." + Style.RESET_ALL)
        exit()

def check_top_leaderboard(headers, session):
    """Mengambil data leaderboard."""
    query_top_leaderboard = {
        "query": "query getTopStatusSnapshots($offset: Int, $limit: Int) { getTopStatusSnapshots(offset: $offset, limit: $limit) { id depositCount totalPoint lastDepositedAt user { id sub name iconPath } inviter { id name } } }",
        "variables": {"offset": 0, "limit": 100},
        "operationName": "getTopStatusSnapshots"
    }
    
    session.post(GRAPHQL_URL, headers=headers, json=query_top_leaderboard)

def execute_grow_action(headers, session):
    """Melakukan Grow Action dan mengambil totalValue dari respons."""
    mutation_execute_grow = {
        "query": "mutation ExecuteGrowAction($withAll: Boolean) { executeGrowAction(withAll: $withAll) { baseValue leveragedValue totalValue multiplyRate } }",
        "variables": {"withAll": True},
        "operationName": "ExecuteGrowAction"
    }

    response = session.post(GRAPHQL_URL, headers=headers, json=mutation_execute_grow)

    if response.status_code == 200:
        grow_data = response.json().get("data", {}).get("executeGrowAction", {})
        total_value = grow_data.get("totalValue", 0)

        print(Fore.GREEN + Style.BRIGHT + f"✅ Draw Successful! Total Points Earned: {total_value}" + Style.RESET_ALL)
        logging.info(f"Grow action success, earned points: {total_value}")

        return total_value
    else:
        print(Fore.RED + "❌ Grow action failed!" + Style.RESET_ALL)
        logging.error(f"Grow action failed: {response.text}")
        return 0

def get_current_user_status(headers, session):
    """Mengambil data terbaru user setelah Grow Action."""
    query_current_user = {
        "query": "query CurrentUserStatus { currentUser { depositCount totalPoint evmAddress { userId address } inviter { id name } } }",
        "operationName": "CurrentUserStatus"
    }

    response = session.post(GRAPHQL_URL, headers=headers, json=query_current_user)

    if response.status_code == 200:
        user_data = response.json().get("data", {}).get("currentUser", {})
        deposit_count = user_data.get("depositCount", 0)
        total_point = user_data.get("totalPoint", 0)

        print(Fore.CYAN + Style.BRIGHT + f"📊 User Stats: Deposit Count: {deposit_count} | Total Points: {total_point}" + Style.RESET_ALL)
        logging.info(f"User stats updated: Deposit Count: {deposit_count}, Total Points: {total_point}")

        return deposit_count, total_point
    else:
        print(Fore.RED + "❌ Failed to get user status!" + Style.RESET_ALL)
        logging.error(f"Failed to get user status: {response.text}")
        return 0, 0

def main():
    """Fungsi utama untuk menjalankan program."""
    print_intro()
    accounts = load_accounts()

    while True:
        for account in accounts:
            refresh_token = account.get("refresh_token")
            proxy = account.get("proxy")

            try:
                # Setup session dengan proxy jika tersedia
                session = requests.Session()
                if proxy:
                    session.proxies = {"http": proxy, "https": proxy}
                    logging.info(f"Connected to proxy: {proxy}")

                # Perbarui token akses
                token_data = refresh_access_token(refresh_token)
                access_token = token_data["access_token"]

                # Ambil headers dari grow_headers.py
                headers = get_grow_headers(access_token)

                print(Fore.CYAN + Style.BRIGHT + f"\nExecuting Grow for account: {account.get('privateKey', 'Unknown')[:6]}..." + Style.RESET_ALL)

                # 1️⃣ Cek Top Leaderboard
                check_top_leaderboard(headers, session)

                # 2️⃣ Jalankan Grow Action
                total_value = execute_grow_action(headers, session)

                # 3️⃣ Ambil Data User Terbaru
                deposit_count, total_point = get_current_user_status(headers, session)

                # 4️⃣ Logging hasil grow
                logging.info(f"Account: {account.get('privateKey', 'Unknown')[:6]} | Total Earned: {total_value} | New Deposit Count: {deposit_count} | New Total Points: {total_point}")

            except Exception as e:
                logging.error(f"Error processing account {account.get('privateKey', 'Unknown')}: {e}")

        # ⏳ Delay 40 menit sebelum siklus berikutnya
        for remaining in range(CYCLE_DELAY, 0, -10):  # Update setiap 10 detik
            print(Fore.YELLOW + Style.BRIGHT + f"Tunggu {remaining // 60} menit {remaining % 60} detik sebelum batch berikutnya..." + Style.RESET_ALL, end="\r")
            time.sleep(10)

if __name__ == "__main__":
    main()
