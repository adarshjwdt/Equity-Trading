import requests
import json
import os

# Use an absolute path to avoid directory issues
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_MAP_FILE = os.path.join(BASE_DIR, 'angel_token_map.json')
TOKEN_URL = "https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json"

def download_token_map():
    """Downloads the latest token map from Angel One."""
    print(f"📥 Downloading Angel One Token Map to {TOKEN_MAP_FILE}...")
    try:
        response = requests.get(TOKEN_URL, timeout=10)
        if response.status_code == 200:
            with open(TOKEN_MAP_FILE, 'w') as f:
                json.dump(response.json(), f)
            print("✅ Token Map Downloaded Successfully")
            return response.json()
        else:
            print(f"❌ Failed to download token map: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to download token map error: {e}")
    return []

def get_token_map():
    """Returns the token map, downloading it if it doesn't exist."""
    if not os.path.exists(TOKEN_MAP_FILE):
        return download_token_map()
    
    with open(TOKEN_MAP_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return download_token_map()

def get_tokens_for_symbols(symbols):
    """
    Given a list of symbols (e.g. ['SBIN-EQ', 'RELIANCE-EQ']),
    returns a list of tokens for the WebSocket.
    Returns: [{"exchangeType": 1, "tokens": ["3045", "2885"]}]
    """
    all_tokens = get_token_map()
    exchange_map = {
        'NSE': 1,   # NSE_CM
        'NFO': 2,   # NSE_FO
        'BSE': 3,   # BSE_CM
        'BFO': 4,   # BSE_FO (Guessing based on pattern)
        'MCX': 5,   # MCX_FO
    }
    
    result = {} # exchange_type -> [tokens]
    
    # Symbols in Angel One's list often look like 'SBIN-EQ' (Symbol-Series)
    # We'll try to match by 'symbol' field in the JSON
    for item in all_tokens:
        sym = item.get('symbol')
        if sym in symbols:
            exch = item.get('exch_seg')
            exch_type = exchange_map.get(exch, 1)
            token = item.get('token')
            
            if exch_type not in result:
                result[exch_type] = []
            result[exch_type].append(token)
            
    return [{"exchangeType": k, "tokens": v} for k, v in result.items()]
