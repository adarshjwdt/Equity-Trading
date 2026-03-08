import pyotp
from kiteconnect import KiteConnect
from SmartApi import SmartConnect
from ..models import BrokerToken

def fetch_all_holdings(selected_clients, all_credentials):
    """Loops through selected clients and fetches data from either Angel or Zerodha."""
    combined_data = []
    
    # Debug: See what we are working with
    print(f"DEBUG: Processing {len(all_credentials)} total credentials for selection: {selected_clients}")
    
    angel_tokens = None
    
    for cred in all_credentials:
        # Standardizing the username/ID from your sheet keys
        user_id = str(cred.get('Client ID') or cred.get('Username') or "")
        
        # Check if this specific client was selected in the Execution Sheet
        if user_id not in selected_clients:
            continue
        
        try:
            # Clean up the broker name for comparison
            broker = str(cred.get('Broker', '')).upper().strip()
            api_key = cred.get('API Key')

            if 'ANGEL' in broker:
                print(f"🚀 Attempting Angel One login for: {user_id}")
                result = _fetch_angel(
                    client_id=user_id,
                    password=str(cred.get('Password') or ""), # Usually your 4-digit MPIN
                    totp_seed=cred.get('TOTP Seed'),
                    api_key=api_key
                )
                holdings = result['holdings']
                # Capture tokens from the first successful Angel login for WebSocket
                if not angel_tokens:
                    angel_tokens = {
                        'auth_token': result['auth_token'],
                        'feed_token': result['feed_token'],
                        'api_key': api_key,
                        'client_code': user_id
                    }
            
            # Flexible matching: Handles 'ZERODHA', 'KITE', 'ZERODHA KITE'
            elif 'ZERODHA' in broker or 'KITE' in broker:
                print(f"🚀 Fetching Zerodha holdings for: {user_id}")
                holdings = _fetch_kite(user_id, api_key)
            
            else:
                print(f"⚠️ Skipping {user_id}: Unknown broker naming convention '{broker}'")
                continue
            
            combined_data.extend(holdings)
            print(f"✅ Successfully fetched {len(holdings)} holdings for {user_id}")

        except Exception as e:
            print(f"❌ Error fetching for {user_id}: {str(e)}")
            
    return {
        'holdings': combined_data,
        'angel_tokens': angel_tokens
    }

def _fetch_angel(client_id, password, totp_seed, api_key):
    """Automated Angel One Login & Holdings Fetch."""
    # Ensure SmartConnect is initialized
    obj = SmartConnect(api_key=api_key)
    
    # 1. Generate 6-digit TOTP on the fly from the Seed
    try:
        token = pyotp.TOTP(totp_seed.replace(" ", "")).now()
    except Exception as e:
        raise Exception(f"Invalid TOTP Seed for {client_id}: {e}")
    
    # 2. Login (Password here is usually your MPIN)
    session = obj.generateSession(client_id, password, token)
    
    if not session.get('status'):
        raise Exception(f"Angel Login Failed: {session.get('message')}")

    # 3. Get Holdings
    res = obj.holding()
    
    # SmartAPI returns 'data' as a list or None
    raw_list = res.get('data', [])
    if raw_list is None:
        raw_list = []
    
    # 4. Get Auth and Feed Token for WebSocket
    auth_token = session.get('data', {}).get('jwtToken')
    feed_token = session.get('data', {}).get('feedToken')

    # Normalize Angel fields to match our internal format
    holdings = [{
        'symbol': h.get('tradingsymbol'),
        'qty': int(float(h.get('quantity', 0))), # Handle string/float quantity
        'price': float(h.get('ltp', 0)),
        'client_id': client_id,
        'broker': 'Angel'
    } for h in raw_list]

    return {
        'holdings': holdings,
        'auth_token': auth_token,
        'feed_token': feed_token
    }

def _fetch_kite(username, api_key):
    """Zerodha Fetch (Requires pre-existing token in DB from kite_callback)."""
    try:
        token_record = BrokerToken.objects.get(username=username, broker_name='Zerodha')
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(token_record.access_token)
        
        holdings = kite.holdings()
        
        # Normalize Zerodha fields
        return [{
            'symbol': h['tradingsymbol'],
            'qty': int(h['quantity']),
            'price': float(h['last_price']),
            'client_id': username,
            'broker': 'Zerodha'
        } for h in holdings]
    except BrokerToken.DoesNotExist:
        raise Exception(f"No active session for {username}. Please login via /kite-login/ first.")
    

