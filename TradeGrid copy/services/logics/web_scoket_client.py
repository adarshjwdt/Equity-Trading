import threading
import time
from SmartApi.smartWebSocketV2 import SmartWebSocketV2

# Global state
live_market_data = {}
_ws_instance = None

def on_data(*args):
    global live_market_data
    # Determine signature (some versions pass wsapp, others don't)
    msg = args[1] if len(args) > 1 else args[0]
    
    # print(f"📡 RAW MSG: {msg}")
    token = msg.get('token')
    price = msg.get('last_traded_price')
    if token and price:
        live_market_data[token] = price / 100
        print(f"📡 TICK: {token} -> {live_market_data[token]}")

def on_open(wsapp, token_list):
    print("🚀 SmartStream WebSocket Connected")
    if token_list:
        print(f"📡 Subscribing to: {token_list}")
        try:
            wsapp.subscribe("fetch_holdings", 1, token_list)
        except Exception as e:
            print(f"❌ Subscription Failed: {e}")

def on_error(*args):
    print(f"❌ WebSocket Error: {args}")

def on_close(*args):
    print(f"🔌 WebSocket Connection Closed: {args}")

def start_angel_stream(auth_token, api_key, client_code, feed_token, token_list):
    global _ws_instance
    
    if _ws_instance:
        try:
            _ws_instance.close_connection()
            time.sleep(1)
        except: pass

    sws = SmartWebSocketV2(auth_token, api_key, client_code, feed_token)

    def on_data(*args):
        global live_market_data
        msg = args[1] if len(args) > 1 else args[0]
        token = msg.get('token')
        price = msg.get('last_traded_price')
        if token is not None and price is not None:
            key = str(token)  # keep keys as string so token_to_symbol lookup matches
            live_market_data[key] = price / 100
            print(f"📡 TICK: {key} -> {live_market_data[key]}")

    def on_open(wsapp):
        print("🚀 SmartStream WebSocket Connected")
        if token_list:
            print(f"📡 Subscribing to: {token_list}")
            # Use the sws instance directly for reliable subscription
            sws.subscribe("fetch_holdings", 1, token_list)

    def on_error(*args):
        print(f"❌ WebSocket Error: {args}")

    def on_close(*args):
        print("🔌 WebSocket Connection Closed")

    sws.on_data = on_data
    sws.on_open = on_open
    sws.on_error = on_error
    sws.on_close = on_close

    threading.Thread(target=sws.connect, daemon=True).start()
    _ws_instance = sws

    # 2. Live Pusher Thread with Enhanced Error Handling
    def run_pusher():
        from ..gsheet_service import GoogleSheetService
        from .token_map import get_token_map
        
        # Build a persistent Token -> Symbol map (Prioritizing NSE for Stocks)
        # Use string keys so WebSocket int tokens match when we look up
        all_tokens = get_token_map()
        token_to_symbol = {}
        for item in all_tokens:
            token = item.get('token')
            sym = item.get('symbol', '')
            exch = item.get('exch_seg')
            if token is not None and sym:
                key = str(token)
                if (key not in token_to_symbol) or (exch == 'NSE'):
                    token_to_symbol[key] = sym
        
        print(f"🚀 Live Price Pusher Started (Mapped {len(token_to_symbol)} tokens)")
        
        consecutive_failures = 0
        max_failures = 3
        
        while True:
            try:
                time.sleep(3)  # Reduced from 5s for more responsive updates
                if not live_market_data:
                    continue
                    
                # Use string token for lookup (WebSocket may send int)
                price_push = {}
                for t, p in live_market_data.items():
                    key = str(t)
                    if key not in token_to_symbol:
                        continue
                    sym = token_to_symbol[key]
                    price_push[sym] = p
                    # Sheet may have -E instead of -EQ (e.g. AONETOTAL-E); send both so match works
                    if sym.endswith('-EQ'):
                        price_push[sym[:-2] + '-E'] = p
                if price_push:
                    print(f"📡 Pushing live prices: {len(price_push)} symbols")
                    success = GoogleSheetService.push_live_prices(price_push)
                    
                    if success:
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_failures:
                            print(f"⚠️ Too many consecutive failures ({max_failures}). Pausing for 30s...")
                            time.sleep(30)
                            consecutive_failures = 0
                            
            except Exception as e:
                print(f"❌ Pusher thread error: {e}")
                consecutive_failures += 1
                time.sleep(5)

    threading.Thread(target=run_pusher, daemon=True).start()


def get_live_price(token, default_price):
    """Returns the live price from cache if available, else default."""
    return live_market_data.get(token, default_price)