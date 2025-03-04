# headers.py

def deposit_headers(bearer_token):
    return {
        "Accept": "application/graphql-response+json, application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7,ms;q=0.6",
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Origin": "https://hanafuda.hana.network",
        "Priority": "u=1, i",
        "Referer": "https://hanafuda.hana.network/",
        "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

def get_draw_headers(bearer_token):
    return {
        "Accept": "application/graphql-response+json, application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7,ms;q=0.6",
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Origin": "https://hanafuda.hana.network",
        "Priority": "u=1, i",
        "Referer": "https://hanafuda.hana.network/",
        "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

def get_grow_headers(bearer_token):
    return {
        "Accept": "application/graphql-response+json, application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7,ms;q=0.6",
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Origin": "https://hanafuda.hana.network",
        "Priority": "u=1, i",
        "Referer": "https://hanafuda.hana.network/",
        "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
