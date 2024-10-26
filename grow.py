import requests
import json
import time
import logging
import os
from colorama import Fore, Style

# Konfigurasi logging
logging.basicConfig(filename='hana_auto_grow.log', level=logging.INFO)

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

def print_intro():
    print(Fore.CYAN + Style.BRIGHT + """Auto Grow for HANA Network One Account""" + Style.RESET_ALL)

def print_success(message):
    print(Fore.GREEN + Style.BRIGHT + message + Style.RESET_ALL)

def print_error(message):
    print(Fore.RED + Style.BRIGHT + message + Style.RESET_ALL)

def print_warning(message):
    print(Fore.YELLOW + Style.BRIGHT + message + Style.RESET_ALL)

def load_tokens_from_file():
    try:
        with open("tokens.json", "r") as token_file:
            return json.load(token_file)
    except FileNotFoundError:
        logging.error("File 'tokens.json' not found.")
        print(Fore.RED + Style.BRIGHT + "File 'tokens.json' tidak ditemukan." + Style.RESET_ALL)
        exit()

def main():
    accounts = load_tokens_from_file()

    print(Fore.BLUE + Style.BRIGHT + "Masukkan Jumlah Grow: " + Style.RESET_ALL)
    try:
        num_iterations = int(input())
        if num_iterations <= 0:
            raise ValueError("The number of iterations must be a positive integer.")
    except ValueError as e:
        logging.error(f"Invalid input: {e}")
        print(Fore.RED + Style.BRIGHT + "Input tidak valid." + Style.RESET_ALL)
        exit()

    while True:
        for account in accounts:
            refresh_token = account['refresh_token']
            try:
                token_data = refresh_access_token(refresh_token)
                access_token = token_data["access_token"]

                url = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }

                for i in range(num_iterations):
                    # Mendapatkan status snapshot teratas
                    query_get_top_status_snapshots = """
                    query getTopStatusSnapshots($offset: Int, $limit: Int) {
                    getTopStatusSnapshots(offset: $offset, limit: $limit) {
                        user {
                        id
                        name
                        }
                    }
                    }
                    """
                    variables_top_status = {"offset": 0, "limit": 100}
                    requests.post(url, headers=headers, json={"query": query_get_top_status_snapshots, "variables": variables_top_status})

                    mutation_issue_grow_action = """
                    mutation issueGrowAction {
                    issueGrowAction
                    }
                    """
                    requests.post(url, headers=headers, json={"query": mutation_issue_grow_action})

                    mutation_commit_grow_action = """
                    mutation commitGrowAction {
                    commitGrowAction
                    }
                    """
                    requests.post(url, headers=headers, json={"query": mutation_commit_grow_action})

                    query_current_user = """
                    query CurrentUser {
                    currentUser {
                        name
                        totalPoint
                    }
                    }
                    """
                    response_current_user = requests.post(url, headers=headers, json={"query": query_current_user})

                    if response_current_user.status_code == 200:
                        current_user_data = response_current_user.json()
                        user_name = current_user_data['data']['currentUser']['name']
                        initial_total_point = current_user_data['data']['currentUser']['totalPoint']

                        mutation_spin = """
                        mutation commitSpinAction {
                        commitSpinAction
                        }
                        """
                        response_spin = requests.post(url, headers=headers, json={"query": mutation_spin})

                        if response_spin.status_code == 200:
                            response_current_user_latest = requests.post(url, headers=headers, json={"query": query_current_user})

                            if response_current_user_latest.status_code == 200:
                                latest_total_point = response_current_user_latest.json()['data']['currentUser']['totalPoint']
                                
                                print(Fore.GREEN + Style.BRIGHT + f"{i + 1}/{num_iterations} | Name: {user_name} | Total Points: {latest_total_point}" + Style.RESET_ALL)

                    # Tunggu sejenak sebelum iterasi berikutnya (opsional)
                    time.sleep(10)  # Tunggu 2 detik sebelum iterasi berikutnya

            except Exception as e:
                logging.error(f"Error refreshing token for account {account['name']}: {e}")
                    
        for remaining in range(30, 0, -1):
            print(Fore.YELLOW + Style.BRIGHT + f"Tunggu {remaining} detik sebelum batch berikutnya..." + Style.RESET_ALL, end="\r")
            time.sleep(1)

if __name__ == "__main__":
    print_intro()
    main()
