import requests

class SheetsEngine:
    # Replace this with the URL you copied during the "Deploy" step in Google Sheets
    WEB_APP_URL = "https://script.google.com/macros/s/YOUR_APPS_SCRIPT_ID/exec"

    def get_master_data(self):
        """Fetches all rows from the 'Masters' sheet via the Bridge."""
        try:
            # We add a parameter to tell the script which sheet we want
            response = requests.get(f"{self.WEB_APP_URL}?action=getMasters", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching Masters: {e}")
            return []

    def get_selected_accounts(self):
        """Fetches specific dashboard cells (E2, G2, etc.) via the Bridge."""
        try:
            response = requests.get(f"{self.WEB_APP_URL}?action=getSelected", timeout=10)
            response.raise_for_status()
            # The bridge will return a list like ["User1", "User2"]
            return response.json()
        except Exception as e:
            print(f"Error fetching selected accounts: {e}")
            return []

    def update_execution_grid(self, matrix_data):
        """Sends calculated data BACK to the 'Execution' sheet."""
        try:
            # We use POST to send the big matrix of data
            payload = {
                "action": "updateGrid",
                "data": matrix_data
            }
            response = requests.post(self.WEB_APP_URL, json=payload, timeout=15)
            return response.json().get("status") == "success"
        except Exception as e:
            print(f"Error updating grid: {e}")
            return False