import os
from pydantic import BaseModel, Field, ValidationError
from typing import List

class Settings(BaseModel):
    WATCHLIST_MODE: str = Field(default="TOP100")
    MANUAL_SYMBOLS: List[str] = Field(default_factory=list)
    MIN_24H_VOLUME_USD: float = 50_000_000
    MIN_24H_PCT: float = 3.0
    MA_PERIOD: int = 20
    RSI_THRESHOLD: float = 55.0
    ATR_PCT_MIN: float = 1.5
    TIMEFRAME: str = "1h"
    TOP_N: int = 5
    LANGUAGE: str = "LV"
    SHORT_FORMAT: bool = True
    ADVICE_ENABLED: bool = Field(default=True)

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_IDS: List[str]

    COINGECKO_BASE: str = "https://api.coingecko.com/api/v3"
    COINBASE_BASE: str = "https://api.exchange.coinbase.com"

    STATE_FILE: str = "last_top.json"

def load_settings() -> 'Settings':
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
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        "TELEGRAM_CHAT_IDS": [x.strip() for x in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if x.strip()],
    }
    try:
        cfg = Settings(**env)
    except ValidationError as e:
        raise SystemExit(f"Config validation error: {e}")

    # 👉 papildus stingrā pārbaude
    if not cfg.TELEGRAM_BOT_TOKEN:
        raise SystemExit("Config error: TELEGRAM_BOT_TOKEN is empty or missing.")
    if not cfg.TELEGRAM_CHAT_IDS:
        raise SystemExit("Config error: TELEGRAM_CHAT_IDS is empty or missing. Provide numeric chat IDs, comma-separated.")

    return cfg
