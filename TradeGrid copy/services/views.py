from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.conf import settings
from kiteconnect import KiteConnect
from .gsheet_service import GoogleSheetService
from .logics.broker_engine import fetch_all_holdings
from .utils import generate_portfolio_grid
from .models import BrokerToken

def sync_all_accounts(request):
    """
    The main trigger: 
    1. Fetches selected IDs from Google Sheet.
    2. Logs into Brokers (Angel/Zerodha).
    3. Fetches Holdings.
    4. Pushes formatted data back to the 'Execution' sheet.
    """
    try:
        # 1. Initialize the Google Sheet Bridge
        service = GoogleSheetService()
        
        # 2. Get the list of IDs selected in the Sheet (e.g., from dropdowns)
        selected_ids = service.fetch_selected_accounts() 
        
        if not selected_ids:
            return JsonResponse({
                "status": "error", 
                "message": "No Client IDs were selected in the Google Sheet."
            }, status=400)
        
        # 3. Fetch credentials (API Keys, TOTP Seeds, etc.) from 'Masters' tab
        creds = service.fetch_master_data()
        
        # 4. Fetch Holdings from Brokers
        fetch_result = fetch_all_holdings(selected_ids, creds)
        raw_holdings = fetch_result['holdings']
        tokens = fetch_result['angel_tokens']

        # 5. Initialize WebSocket if tokens are available
        if tokens:
            from .logics.web_scoket_client import start_angel_stream
            from .logics.token_map import get_tokens_for_symbols
            
            # Extract unique symbols to subscribe
            symbols = list(set([h['symbol'] for h in raw_holdings if h['broker'] == 'Angel']))
            print(f"🔍 Symbols to subscribe: {symbols}")
            token_list = get_tokens_for_symbols(symbols)
            print(f"🔍 Tokens mapped: {token_list}")
            
            if token_list:
                print(f"📡 Starting WebSocket for symbols: {symbols}")
                start_angel_stream(
                    auth_token=tokens['auth_token'],
                    api_key=tokens['api_key'],
                    client_code=tokens['client_code'],
                    feed_token=tokens['feed_token'],
                    token_list=token_list
                )
            else:
                print("⚠️ No tokens found for symbols. WebSocket not started.")
        else:
            print("⚠️ No Angel tokens available. WebSocket skipped.")

        # 6. Format portfolio grid for the Execution sheet (Portfolio layout)
        final_matrix = generate_portfolio_grid(raw_holdings, selected_ids)
        
        # --- DEBUGGING AREA ---
        print(f"🚀 Selected IDs: {selected_ids}")
        print(f"📊 Raw Holdings Count: {len(raw_holdings)}")
        # ----------------------

        if not final_matrix:
            # If login worked but there are literally 0 stocks in all accounts
            return JsonResponse({
                "status": "warning", 
                "message": "Logins successful, but no holdings found to display."
            })

        # 6. Push data back to Google Sheets via Apps Script POST
        update_success = service.update_execution_grid(final_matrix)
        
        if update_success:
            return JsonResponse({
                "status": "complete", 
                "message": f"Successfully synced {len(selected_ids)} accounts.",
                "synced": selected_ids
            })
        else:
            return JsonResponse({
                "status": "error", 
                "message": "Django fetched data, but Google Apps Script failed to write it to the cells."
            }, status=500)

    except BrokerToken.DoesNotExist:
        return JsonResponse({
            "status": "error", 
            "message": "Zerodha session expired. Please login via /kite-login/ first."
        }, status=401)
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return JsonResponse({
            "status": "error", 
            "message": f"Sync failed: {str(e)}"
        }, status=500)

def get_live_prices(request):
    """
    Lightweight endpoint for high-frequency polling.
    Returns: { "SYMBOL": Price, ... }
    """
    from .logics.web_scoket_client import live_market_data
    from .logics.token_map import get_token_map
    
    # 1. Get the token map
    all_tokens = get_token_map()
    
    # 2. Reverse map: Token -> Symbol
    # In a production app, you'd cache this reverse map
    token_to_symbol = {item['token']: item['symbol'] for item in all_tokens}
    
    # 3. Build response matching symbols to live prices
    response_data = {}
    for token, price in live_market_data.items():
        symbol = token_to_symbol.get(token)
        if symbol:
            response_data[symbol] = price
            
    return JsonResponse(response_data)



# --- ZERODHA AUTHENTICATION FLOW ---

def kite_login(request):
    """Redirects user to Zerodha's login page."""
    kite = KiteConnect(api_key=settings.KITE_API_KEY)
    return redirect(kite.login_url())

def kite_callback(request):
    """Handles the redirect back from Zerodha and saves the Access Token."""
    request_token = request.GET.get("request_token")
    try:
        kite = KiteConnect(api_key=settings.KITE_API_KEY)
        data = kite.generate_session(request_token, api_secret=settings.KITE_API_SECRET)
        
        # Save or Update the token in our database
        BrokerToken.objects.update_or_create(
            username=data['user_id'],
            broker_name='Zerodha',
            defaults={'access_token': data['access_token']}
        )
        return HttpResponse("🚀 Zerodha Token Saved! You can now sync from Google Sheets.")
    except Exception as e:
        return HttpResponse(f"Login Error: {e}")