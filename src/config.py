import os
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

class Settings(BaseModel):
    # Filters & logic
    WATCHLIST_MODE: str = Field(default="TOP100")  # TOP100 or MANUAL
    MANUAL_SYMBOLS: List[str] = Field(default_factory=list)  # if WATCHLIST_MODE=MANUAL
    MIN_24H_VOLUME_USD: float = 50_000_000
    MIN_24H_PCT: float = 3.0
    MA_PERIOD: int = 20
    RSI_THRESHOLD: float = 55.0
    ATR_PCT_MIN: float = 1.5
    TIMEFRAME: str = "1h"  # '1h' | '4h' | '15m'
    TOP_N: int = 5
    LANGUAGE: str = "LV"   # 'LV' or 'EN'
    SHORT_FORMAT: bool = True

    # Advice (entry/SL/TP) toggle
    ADVICE_ENABLED: bool = Field(default=True)

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_IDS: List[str]  # comma-separated input -> list

    # Runtime
    COINGECKO_BASE: str = "https://api.coingecko.com/api/v3"
    COINBASE_BASE: str = "https://api.exchange.coinbase.com"

    # State
    STATE_FILE: str = "last_top.json"

def load_settings() -> Settings:
    env = {
        "WATCHLIST_MODE": os.getenv("WATCHLIST_MODE", "TOP100").upper(),
        "MANUAL_SYMBOLS": [s.strip().upper() for s in os.getenv("MANUAL_SYMBOLS", "").split(",") if s.strip()],
        "MIN_24H_VOLUME_USD": float(os.getenv("MIN_24H_VOLUME_USD", "50000000")),
        "MIN_24H_PCT": float(os.getenv("MIN_24H_PCT", "3.0")),
        "MA_PERIOD": int(os.getenv("MA_PERIOD", "20")),
        "RSI_THRESHOLD": float(os.getenv("RSI_THRESHOLD", "55")),
        "ATR_PCT_MIN": float(os.getenv("ATR_PCT_MIN", "1.5")),
        "TIMEFRAME": os.getenv("TIMEFRAME", "1h"),
        "TOP_N": int(os.getenv("TOP_N", "5")),
        "LANGUAGE": os.getenv("LANGUAGE", "LV").upper(),
        "SHORT_FORMAT": os.getenv("SHORT_FORMAT", "true").lower() == "true",
        "ADVICE_ENABLED": os.getenv("ADVICE_ENABLED", "true").lower() == "true",
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_CHAT_IDS": [x.strip() for x in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if x.strip()],
    }
    try:
        return Settings(**env)
    except ValidationError as e:
        raise SystemExit(f"Config validation error: {e}")
