# TradeGrid - Real-Time Portfolio Dashboard

A Django-based trading system that provides real-time portfolio synchronization between multiple brokers (Angel One, Zerodha) and Google Sheets.

## Architecture

```
Google Sheets ←→ Django Web App ←→ Broker APIs
                    ↓
               WebSocket Client ←→ Market Data
```

## Features

- **Multi-Broker Support**: Angel One (SmartAPI) and Zerodha (KiteConnect)
- **Real-Time Updates**: WebSocket-based live price streaming
- **Google Sheets Integration**: Automatic portfolio synchronization
- **Automated Authentication**: TOTP-based login for Angel One
- **Error Recovery**: Robust reconnection and retry logic

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Google Sheets

1. Copy `GOOGLE_APPS_SCRIPT.md` code to Google Apps Script
2. Deploy as Web App and copy the URL
3. Update `WEB_APP_URL` in `services/gsheet_service.py`
4. Set up your Google Sheet with "Masters" and "Execution" tabs

### 3. Configure Broker Credentials

Edit `services/gsheet_service.py` or use environment variables:

```python
# For Angel One
{
    "Name": "Your Name",
    "Broker": "Angel One", 
    "Client ID": "YOUR_CLIENT_ID",
    "API Key": "YOUR_API_KEY",
    "TOTP Seed": "YOUR_TOTP_SEED",
    "Password": "YOUR_MPIN"
}
```

### 4. Run Django Server

```bash
cd TradeGrid
python manage.py runserver
```

### 5. Initialize System

1. **Zerodha Login**: Visit `http://localhost:8000/kite-login/`
2. **Sync Portfolio**: Trigger sync from your Google Sheet or call API endpoint

## API Endpoints

- `GET /kite-login/` - Redirect to Zerodha login
- `GET /kite_callback/` - Handle Zerodha OAuth callback
- `POST /sync_all_accounts/` - Main portfolio synchronization
- `GET /get_live_prices/` - Get current market prices

## Configuration

### Environment Variables

```bash
GSCRIPT_WEB_APP_URL=your_web_app_url
WEBSOCKET_RECONNECT_DELAY=5
PRICE_UPDATE_INTERVAL=3
DEBUG=True
```

### File Structure

```
TradeGrid/
├── services/
│   ├── models.py          # Django models
│   ├── views.py           # Main API endpoints
│   ├── gsheet_service.py  # Google Sheets integration
│   ├── config.py          # Configuration management
│   └── logics/
│       ├── broker_engine.py    # Broker authentication
│       ├── web_socket_client.py # Real-time data
│       └── token_map.py        # Symbol-token mapping
├── TradeGrid/
│   ├── settings.py        # Django settings
│   └── urls.py           # URL routing
└── requirements.txt       # Python dependencies
```

## Real-Time Data Flow

1. **Portfolio Sync**: Fetch holdings from brokers → Format data → Update Google Sheets
2. **WebSocket Stream**: Connect to Angel One WebSocket → Receive price ticks → Push to Google Sheets
3. **Price Updates**: Every 3 seconds → Send latest prices → Update sheet cells

## Error Handling

- **Automatic Reconnection**: WebSocket reconnection on connection loss
- **Retry Logic**: Exponential backoff for failed requests
- **Rate Limiting**: Handles API rate limits gracefully
- **Fallback**: Uses cached data on temporary failures

## Security

- **TOTP Authentication**: Secure Angel One login
- **OAuth Flow**: Standard Zerodha authentication
- **Private Web App URL**: Keep Apps Script URL confidential
- **Environment Variables**: Store sensitive data in environment

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check Angel One credentials
   - Verify TOTP seed is correct
   - Ensure feed token is valid

2. **Google Sheet Updates Failing**
   - Verify Apps Script deployment
   - Check Web App URL in config
   - Ensure sheet has correct structure

3. **Zerodha Login Issues**
   - Complete OAuth flow via `/kite-login/`
   - Check API key and secret in settings

### Debug Mode

Enable debug logging:
```python
# In config.py
DEBUG = True
LOG_LEVEL = "DEBUG"
```

## Development

### Adding New Brokers

1. Create authentication function in `broker_engine.py`
2. Add broker-specific data normalization
3. Update token mapping if needed

### Customizing Sheet Updates

Modify `gsheet_service.py`:
- `update_execution_grid()` for bulk updates
- `push_live_prices()` for real-time prices

## Production Deployment

- Use environment variables for all configuration
- Set up proper logging and monitoring
- Consider adding API key authentication
- Implement rate limiting and caching

## License

MIT License - see LICENSE file for details
