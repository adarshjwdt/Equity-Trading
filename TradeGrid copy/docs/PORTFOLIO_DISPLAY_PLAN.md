# Portfolio display plan: Masters-driven, target layout

## Goal

1. **Stop hardcoding** – Fetch account list and credentials from the **Masters** sheet (tbl_Accounts: Account Holder Name, Broker, Username, API Key, API Secret).
2. **Display** – Render the **Portfolio** section on the Execution sheet in the target layout: one row per scrip, one **Price** column, then per-account **Qty** and **Value** columns in Masters order.

---

## Current vs target

| Aspect | Current (TRADER Execution) | Target (Portfolio layout) |
|--------|-----------------------------|---------------------------|
| Account list | Hardcoded in `gsheet_service` | From Masters tab (Username, Broker, API Key, API Secret) |
| Credentials | Hardcoded in `fetch_master_data()` | From Masters tab rows |
| Grid shape | [Symbol, LTP, Qty1, Val1, Qty2, Val2, ...] flat | Header: "Account" + account names; subheader: "Scrips", "HOLDINGS", "Price", "Qty", "Value" per account; then data rows |
| Price column | Single LTP column | Single Price column (column D in target); live updates go here |

---

## Masters sheet (source of truth)

- **Tab name:** `Masters` (or the name of the sheet that has tbl_Accounts).
- **Columns (your screenshot):** Account Holder Name, Broker, Username, API Key, API Secret.
- **Use:** Each row = one profile. We use **Username** as the account id (e.g. TB987, TAB345, 12456790). For Zerodha we need **API Key** and **API Secret** (and a prior login via `/kite-login/` per account to store `BrokerToken`). Rows with empty Username or empty API Key (for that broker) can be skipped for sync.

Mapping to existing broker_engine:

- `Client ID` / `Username` ← Masters **Username**
- `Broker` ← Masters **Broker**
- `API Key` ← Masters **API Key**
- For Zerodha session: we already use `BrokerToken` (from kite_callback). For **multi-account Zerodha** with different API keys, each account must complete `/kite-login/` once; we can use **API Secret** from Masters when implementing per-account session generation later if needed.
- Angel One: current code expects TOTP Seed + Password; your Masters doesn’t have those. So **Phase 1 = Zerodha-only from Masters**; Angel can stay hardcoded or we add columns (TOTP Seed, Password) later.

---

## Plan (phased)

### Phase 1: Read Masters from the sheet (no more hardcoding)

**1.1 Apps Script – expose Masters data**

- In the deployed Apps Script, extend **doGet** to support a query parameter, e.g. `?action=getMasters`.
- When `action=getMasters`: read the **Masters** tab (e.g. `getSheetByName('Masters')`), get all values with `getDataRange().getValues()`, then return JSON: first row = headers, rest = rows. So Python gets e.g.  
  `{ "headers": ["Account Holder Name", "Broker", "Username", "API Key", "API Secret"], "rows": [ ["Gopala Krishnan R", "Zerodha", "GTJ171", "mhqq...", "ifl4..."], ... ] }`.
- Optional: `?action=getSelected` to read which accounts to include (e.g. from a dropdown or checkbox column in Masters). If not implemented, “selected” = all rows that have Username and (for Zerodha) API Key.

**1.2 Python – call Apps Script to get Masters**

- In **gsheet_service** (or a small helper):
  - Add a method e.g. `fetch_master_from_sheet()` that GETs `WEB_APP_URL?action=getMasters`, parses JSON, and returns a list of dicts: each dict = one row with keys = header names (e.g. "Username", "Broker", "API Key", "API Secret", "Account Holder Name").
- Replace **fetch_master_data()** so it uses this (with a fallback to empty list or current hardcoded list if GET fails, so dev doesn’t break).
- **fetch_selected_accounts()**: either call `?action=getSelected` if you add it, or derive from Masters: return list of **Username** for rows that have Username and (for Zerodha) API Key non-empty.

**1.3 Map Masters row → broker_engine credentials**

- broker_engine expects keys like: `Client ID`, `Broker`, `API Key`, and for Zerodha it uses stored token (no API Secret in the current fetch path). So when building `creds` for `fetch_all_holdings(selected_ids, creds)`:
  - For each Masters row: `{ "Client ID": row["Username"], "Username": row["Username"], "Broker": row["Broker"], "API Key": row["API Key"] }`. Add "API Secret" if you later do per-account Zerodha login from backend.
- Pass `creds` = list of these dicts; `selected_ids` = list of Usernames to sync (from step 1.2).

Result: **Account list and credentials come from the sheet; no hardcoded list of IDs or creds.**

---

### Phase 2: Build the portfolio grid in the target layout

**2.1 Define the exact grid shape (Execution sheet)**

- **Row 1 (optional):** Login / Auth Status, "✅ ACTIVE (HH:MM:SS)" – can be written by script or left to formula/separate process.
- **Row 2:** `["Portfolio", "", "Account", account1, account2, account3, account4]` – account order = order of selected accounts from Masters.
- **Row 3:** `["Scrips", "HOLDINGS", "Price", "Qty", "Value", "Qty", "Value", "Qty", "Value", "Qty", "Value"]` – one "Qty", "Value" pair per account.
- **Row 4+:** For each scrip (sorted): `["", symbol, price, qty1, val1, qty2, val2, qty3, val3, qty4, val4]`. Use 0 where an account doesn’t hold that scrip.
- **Next row:** Total row: `["", "", "Total", total_qty1, total_val1, ...]` (optional; can be formula on sheet instead).
- **Ledger / POSITIONS:** Same as now; can be fixed rows below the grid or left to you.

**2.2 New (or extended) matrix builder in Python**

- Add a function, e.g. **generate_portfolio_grid(holdings_list, account_order)**:
  - Input: `holdings_list` = list of `{ symbol, qty, price, client_id, broker }` (existing format from `fetch_all_holdings`); `account_order` = list of account ids in display order (e.g. `["TB987", "TAB345", "TB987", "12456790"]` = order from Masters).
  - Build a pivot: (symbol × account) → (qty, value). Use same price logic as now (snapshot or live from WebSocket if you already have it).
  - Build:
    - Header row 1: `["Portfolio", "", "Account"] + account_order`
    - Header row 2: `["Scrips", "HOLDINGS", "Price"] + (for each account: ["Qty", "Value"])`
    - Data rows: for each symbol in sorted order, one row `["", symbol, price, qty1, val1, qty2, val2, ...]`
  - Return 2D list (same format as current `generate_matrix` so it can be sent to the same `update_execution_grid`).

- **Views:** In `sync_all_accounts`, after `fetch_all_holdings` and getting `raw_holdings` and `selected_ids` (now from Masters), call `generate_portfolio_grid(raw_holdings, selected_ids)` instead of (or in addition to) `generate_matrix`, and send that to **update_execution_grid**. So the Execution sheet receives the new layout.

**2.3 Apps Script – write the grid**

- **updateExecutionGrid** already clears from row 2 and writes `matrixData` starting at row 2. So you can keep it as-is: Python sends the full grid (including "Portfolio", "Account", "Scrips", "HOLDINGS", "Price", then data). Only ensure the matrix has enough columns for all accounts (e.g. 3 + 2*N for N accounts).
- If you want **Login / Auth Status** on row 1, either:
  - Python sends it as the first row of the matrix and the script writes starting at row 1, or
  - Script writes grid starting at row 2 and you keep row 1 for status (e.g. formula or a separate small update). Plan assumes grid starts at row 2; row 1 can be reserved for status.

---

### Phase 3: Live price updates on the new layout

- **updateLivePrices** in Apps Script must find the **Symbol** and **Price** columns in the new layout. In the target, the “scrip” column is **HOLDINGS** (column B) and **Price** is column C (or D depending on where “Account” row is). So:
  - Either ensure the row that contains "Price" and "HOLDINGS" (or "Scrips") is used as the header row for column detection (e.g. scan rows until you find a row with both "Price" and "HOLDINGS"/"Scrips"/"Symbol"), then set symbolCol and priceCol from that row.
  - Or in the script, look for column where header (string) includes `'price'` or `'ltp'`, and for symbol includes `'holdings'` or `'symbol'` or `'scrips'`, so it works for both the old Execution layout and the new Portfolio layout.
- No change needed on the Python side for pushing prices: we still send `{ "SYMBOL": price, ... }`; only the script’s column detection must match the new header row.

---

## Implementation order (summary)

1. **Apps Script:** Add `getMasters` (and optionally `getSelected`) in doGet; return Masters tab as JSON.
2. **Python gsheet_service:** Add `fetch_master_from_sheet()`; make `fetch_master_data()` and `fetch_selected_accounts()` use it; map Masters columns to broker_engine format (Username → Client ID, etc.).
3. **Python utils:** Add `generate_portfolio_grid(holdings_list, account_order)` that outputs the target grid (Portfolio/Account header, Scrips/HOLDINGS/Price, Qty/Value per account, data rows).
4. **Python views:** Use Masters-driven creds and selected_ids; call `generate_portfolio_grid` and send result to `update_execution_grid`.
5. **Apps Script updateLivePrices:** Make symbol/price column detection work for the new header row (e.g. "HOLDINGS" and "Price").

After this, the **portfolio part** is driven entirely from the Masters sheet and displayed in the target layout; you don’t need to hardcode accounts or credentials, and the sheet remains view-only for you.

---

## Notes

- **Zerodha:** Each account (Username) must have completed `/kite-login/` once so `BrokerToken` exists; then sync will use that token. For multiple Zerodha apps (different API Key/Secret per row), you’ll need to use that row’s API Key/Secret when generating the session (future enhancement if needed).
- **Dhan / Groww:** broker_engine currently only has Angel and Zerodha. Adding Dhan/Groww would require new broker branches and their APIs; out of scope for “portfolio display only” here.
- **Total / Ledger:** Can be computed in Python and appended as extra rows in the grid, or as formulas in the sheet; your choice.
