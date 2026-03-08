import requests
import time

class GoogleSheetService:
    # Update this with your current Web App URL from Apps Script
    WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzk-4Vz0aVY-wiwoNHAQhMrgzwrWNcBovjupHGz0axqNajYCWpnoI_tT28pSQcKjvJxmA/exec"

    @classmethod
    def fetch_selected_accounts(cls):
        """Hardcoded for now to bypass Workspace login issues."""
        return ["AACD494945"]

    @classmethod
    def fetch_master_data(cls):
        """Provides credentials. indention is crucial here."""
        return [{
            "Name": "Adarsh",
            "Broker": "Angel One",
            "Client ID": "AACD494945",
            "API Key": "1AAgO1Su",
            "TOTP Seed": "JJXNRYTJLX5DL264LQCHYBEBQE",
            "Password": "0987"  # Your 4-digit MPIN
        }]

    @classmethod
    def update_execution_grid(cls, master_data):
        """Sends fetched stock data back to the Google Sheet."""
        try:
            payload = {
                "action": "updateGrid",
                "data": master_data
            }
            response = requests.post(cls.WEB_APP_URL, json=payload, timeout=30)
            print(f"DEBUG: Sheet Update Status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"DEBUG: Sheet Update Error: {e}")
            return False

    @classmethod
    def push_live_prices(cls, price_data):
        """Sends lightweight price updates to the Google Sheet (Sub-sync) with retry logic."""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                payload = {
                    "action": "updatePricesOnly",
                    "prices": price_data
                }
                # Low timeout for high-frequency pushes
                response = requests.post(cls.WEB_APP_URL, json=payload, timeout=8)
                print(f"DEBUG: Live Price Push Status: {response.status_code}")
                
                if response.status_code == 200:
                    return True
                elif response.status_code == 429:  # Rate limited
                    print(f"⚠️ Rate limited, waiting {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    print(f"DEBUG: Unexpected response: {response.text}")
                    
            except requests.exceptions.Timeout:
                print(f"DEBUG: Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    continue
            except Exception as e:
                print(f"DEBUG: Live Price Push Error: {e}")
                if attempt < max_retries - 1:
                    continue
                    
        return False