import pandas as pd
import numpy as np
from datetime import datetime

def generate_matrix(holdings_list, selected_clients):
    """
    Transforms raw list of holdings into a structured grid for Google Sheets.
    Final Row Format: [Symbol, LTP, Qty1, Val1, Qty2, Val2, Qty3, Val3, Qty4, Val4, Qty5, Val5]
    """
    if not holdings_list:
        return []

    # 1. Convert raw list to a DataFrame
    df = pd.DataFrame(holdings_list)
    
    # Ensure numeric types for calculation
    df['qty'] = pd.to_numeric(df['qty'], errors='coerce').fillna(0)
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    df['value'] = df['qty'] * df['price']

    # 2. Pivot the data
    pivot = df.pivot_table(
        index='symbol',
        columns='client_id',
        values=['qty', 'value'],
        aggfunc='sum'
    ).fillna(0)

    # 3. Get the most recent Price (LTP) per symbol
    price_map = df.groupby('symbol')['price'].last().to_dict()

    # 4. Construct the Final Grid
    final_grid = []
    
    # WebSocket integration: Try to get live prices
    from .logics.web_scoket_client import live_market_data
    from .logics.token_map import get_tokens_for_symbols
    
    # We define a fixed number of slots (e.g., 5) to match your Sheet UI
    # If selected_clients has fewer than 5, we fill the rest with zeros.
    MAX_CLIENT_SLOTS = 5 
    
    for symbol in sorted(pivot.index):
        # 4a. Get snapshot price
        snapshot_price = price_map.get(symbol, 0)
        
        # 4b. Check if we have a live price from WebSocket
        # Note: This is slightly expensive if done in a loop, but okay for ~50-100 symbols
        token_info = get_tokens_for_symbols([symbol])
        live_price = snapshot_price
        if token_info:
            token = token_info[0]['tokens'][0] # Take first token
            live_price = live_market_data.get(token, snapshot_price)
            if live_price != snapshot_price:
                print(f"🔥 LIVE PRICE USED for {symbol}: {live_price}")

        # Start row with Symbol and its current LTP
        row = [symbol, live_price]
        
        # Loop through the slots (1 to 5)
        for i in range(MAX_CLIENT_SLOTS):
            if i < len(selected_clients):
                client = selected_clients[i]
                # Check if this specific client holds this specific stock
                if client in pivot.columns.get_level_values(1):
                    qty = pivot.loc[symbol, ('qty', client)]
                    val = pivot.loc[symbol, ('value', client)]
                    row.extend([int(qty), round(float(val), 2)])
                else:
                    row.extend([0, 0])
            else:
                # This slot wasn't selected in the sheet, fill with 0s
                row.extend([0, 0])
        
        final_grid.append(row)

    return final_grid


def generate_portfolio_grid(holdings_list, selected_clients):
    """
    Builds the Portfolio section grid to match the Execution sheet layout:
    - Row 0: Portfolio, "", Account, account1, account2, ...
    - Row 1: Scrips, HOLDINGS, Price, Qty, Value, Qty, Value, ... (one Qty/Value per account)
    - Data rows: "", symbol, price, qty1, val1, qty2, val2, ...
    - Total row, Ledger row, then Total Value, POSITIONS section.
    """
    if not holdings_list:
        return _portfolio_grid_empty(selected_clients)

    df = pd.DataFrame(holdings_list)
    df['qty'] = pd.to_numeric(df['qty'], errors='coerce').fillna(0)
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    df['value'] = df['qty'] * df['price']

    pivot = df.pivot_table(
        index='symbol',
        columns='client_id',
        values=['qty', 'value'],
        aggfunc='sum'
    ).fillna(0)

    price_map = df.groupby('symbol')['price'].last().to_dict()

    from .logics.web_scoket_client import live_market_data
    from .logics.token_map import get_tokens_for_symbols

    # Account order; support up to 5 slots like the sheet image
    account_order = list(selected_clients)[:5] if selected_clients else []
    n_accounts = len(account_order)
    num_cols = 3 + 2 * n_accounts  # Scrips, HOLDINGS, Price + (Qty, Value) per account

    grid = []

    # Row 0: Login / Auth Status, "", ✅ ACTIVE (HH:MM:SS)
    now = datetime.now().strftime("%H:%M:%S")
    status_row = (["Login / Auth Status", "", "✅ ACTIVE (" + now + ")"] + [""] * num_cols)[:num_cols]
    grid.append(status_row)

    # Row 1: Portfolio, "", Account, account1, account2, ... (pad to num_cols)
    row0 = (["Portfolio", "", "Account"] + account_order + [""] * num_cols)[:num_cols]
    grid.append(row0)

    # Row 2: Scrips, HOLDINGS, Price, Qty, Value, Qty, Value, ...
    row1 = ["Scrips", "HOLDINGS", "Price"]
    for _ in account_order:
        row1.extend(["Qty", "Value"])
    row1 = (row1 + [""] * num_cols)[:num_cols]
    grid.append(row1)

    # Data rows
    totals_value = [0.0] * n_accounts
    for symbol in sorted(pivot.index):
        snapshot_price = price_map.get(symbol, 0)
        live_price = snapshot_price
        try:
            token_info = get_tokens_for_symbols([symbol])
            if token_info and token_info[0].get('tokens'):
                tok = token_info[0]['tokens'][0]
                live_price = live_market_data.get(str(tok), snapshot_price)
        except Exception:
            pass

        row = ["", symbol, round(float(live_price), 2)]
        for i, client in enumerate(account_order):
            if client in pivot.columns.get_level_values(1):
                qty = int(pivot.loc[symbol, ('qty', client)])
                val = float(pivot.loc[symbol, ('value', client)])
                row.extend([qty, round(val, 2)])
                totals_value[i] += val
            else:
                row.extend([0, 0])
        row = (row + [""] * num_cols)[:num_cols]
        grid.append(row)

    # Total row
    total_row = ["", "Total", ""]
    for i in range(n_accounts):
        total_row.extend(["", round(totals_value[i], 2)])
    total_row = (total_row + [""] * num_cols)[:num_cols]
    grid.append(total_row)

    # Ledger row (no data from holdings; leave blank)
    ledger_row = (["", "Ledger", ""] + [""] * (2 * n_accounts) + [""] * num_cols)[:num_cols]
    grid.append(ledger_row)

    # Empty row
    grid.append([""] * num_cols)

    # Total Value label row (A22 in sheet)
    grid.append((["Total Value"] + [""] * (num_cols - 1))[:num_cols])

    # POSITIONS section
    grid.append((["", "POSITIONS"] + [""] * (num_cols - 2))[:num_cols])
    grid.append([""] * num_cols)  # placeholder for position rows e.g. RELIANCE

    return grid


def _portfolio_grid_empty(selected_clients):
    """Empty portfolio grid with same structure (no holdings)."""
    account_order = list(selected_clients)[:5] if selected_clients else []
    n_accounts = len(account_order)
    num_cols = max(3 + 2 * n_accounts, 13)

    def pad(row, n):
        return (list(row) + [""] * n)[:n]

    now = datetime.now().strftime("%H:%M:%S")
    grid = [
        pad(["Login / Auth Status", "", "✅ ACTIVE (" + now + ")"], num_cols),
        pad(["Portfolio", "", "Account"] + account_order, num_cols),
        pad(["Scrips", "HOLDINGS", "Price"] + (["Qty", "Value"] * n_accounts), num_cols),
        pad(["", "Total", ""] + [""] * (2 * n_accounts), num_cols),
        pad(["", "Ledger", ""] + [""] * (2 * n_accounts), num_cols),
        [""] * num_cols,
        pad(["Total Value"], num_cols),
        pad(["", "POSITIONS"], num_cols),
        [""] * num_cols,
    ]
    return grid