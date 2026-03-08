"""
Configuration management for TradeGrid system
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class TradingConfig:
    
    """Centralized configuration for trading system"""
    
    # Google Sheet Configuration
    GSCRIPT_WEB_APP_URL: str = "https://script.google.com/macros/s/AKfycbxzwTtyZ9r3Nqr-cJsamJL45hebDYTe01DlX-ENDBmm9iAW7BNvoVqvhaWBoO5La1Qufg/exec"
    
    # WebSocket Configuration
    WEBSOCKET_RECONNECT_DELAY: int = 5  # seconds
    PRICE_UPDATE_INTERVAL: int = 3  # seconds (reduced from 5)
    MAX_CONSECUTIVE_FAILURES: int = 3
    FAILURE_PAUSE_DURATION: int = 30  # seconds
    
    # API Configuration
    REQUEST_TIMEOUT: int = 30  # seconds for main requests
    LIVE_PRICE_TIMEOUT: int = 8  # seconds for price updates
    MAX_RETRY_ATTEMPTS: int = 2
    
    # Rate Limiting
    RATE_LIMIT_BACKOFF_BASE: int = 2  # exponential backoff base
    
    # Development Settings
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Default Account (for development)
    DEFAULT_ACCOUNT_ID: str = "AACD494945"
    
    @classmethod
    def get_environment_config(cls) -> 'TradingConfig':
        """Load configuration from environment variables"""
        return TradingConfig(
            GSCRIPT_WEB_APP_URL=os.getenv('GSCRIPT_WEB_APP_URL', cls.GSCRIPT_WEB_APP_URL),
            WEBSOCKET_RECONNECT_DELAY=int(os.getenv('WEBSOCKET_RECONNECT_DELAY', cls.WEBSOCKET_RECONNECT_DELAY)),
            PRICE_UPDATE_INTERVAL=int(os.getenv('PRICE_UPDATE_INTERVAL', cls.PRICE_UPDATE_INTERVAL)),
            MAX_CONSECUTIVE_FAILURES=int(os.getenv('MAX_CONSECUTIVE_FAILURES', cls.MAX_CONSECUTIVE_FAILURES)),
            FAILURE_PAUSE_DURATION=int(os.getenv('FAILURE_PAUSE_DURATION', cls.FAILURE_PAUSE_DURATION)),
            REQUEST_TIMEOUT=int(os.getenv('REQUEST_TIMEOUT', cls.REQUEST_TIMEOUT)),
            LIVE_PRICE_TIMEOUT=int(os.getenv('LIVE_PRICE_TIMEOUT', cls.LIVE_PRICE_TIMEOUT)),
            MAX_RETRY_ATTEMPTS=int(os.getenv('MAX_RETRY_ATTEMPTS', cls.MAX_RETRY_ATTEMPTS)),
            DEBUG=os.getenv('DEBUG', 'True').lower() == 'true',
            LOG_LEVEL=os.getenv('LOG_LEVEL', cls.LOG_LEVEL),
            DEFAULT_ACCOUNT_ID=os.getenv('DEFAULT_ACCOUNT_ID', cls.DEFAULT_ACCOUNT_ID)
        )

# Global configuration instance
config = TradingConfig.get_environment_config()
