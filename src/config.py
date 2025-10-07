import os
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict

class Settings(BaseModel):
    # Primārie slēdži
    WATCHLIST_MODE: str = Field(default="TOP100")  # TOP100 | MANUAL
    MANUAL_SYMBOLS: List[str] = Field(default_factory=list)
    TIMEFRAME: str = "1h"  # 15m | 1h | 4h
    TOP_N: int = 5

    # Formāts / valoda
    LANGUAGE: str = "LV"   # LV | EN (pašlaik lietojam LV)
    SHORT_FORMAT: bool = True
    LONG_FORMAT: bool = False     # ja true, pievieno salīdzinājumu ar iepriekšējo topu
    DETAIL_EMOJI: bool = True     # rādīt ↑/↓/= bultiņas

    # Bāzes (fallback) sliekšņi
    MIN_24H_VOLUME_USD: float = 50_000_000
    MIN_24H_PCT: float = 3.0
    MA_PERIOD: int = 20
    RSI_THRESHOLD: float = 55.0
    ATR_PCT_MIN: float = 1.5

    # Dinamiskie sliekšņi pēc TF (ja nav norādīti, izmantos bāzes)
    # 15m
    MIN_24H_VOLUME_USD_15M: float | None = None
    MIN_24H_PCT_15M: float | None = None
    MA_PERIOD_15M: int | None = None
    RSI_THRESHOLD_15M: float | None = None
    ATR_PCT_MIN_15M: float | None = None
    # 1h
    MIN_24H_VOLUME_USD_1H: float | None = None
    MIN_24H_PCT_1H: float | None = None
    MA_PERIOD_1H: int | None = None
    RSI_THRESHOLD_1H: float | None = None
    ATR_PCT_MIN_1H: float | None = None
    # 4h
    MIN_24H_VOLUME_USD_4H: float | None = None
    MIN_24H_PCT_4H: float | None = None
    MA_PERIOD_4H: int | None = None
    RSI_THRESHOLD_4H: float | None = None
    ATR_PCT_MIN_4H: float | None = None

    # Advice (entry/SL/TP)
    ADVICE_ENABLED: bool = True

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_IDS: List[str]

    # Avoti
    COINGECKO_BASE: str = "https://api.coingecko.com/api/v3"
    COINBASE_BASE: str = "https://api.exchange.coinbase.com"

    # State
    STATE_FILE: str = "last_top.json"  # saglabāsim rangu arī

def _env_list(name: str) -> List[str]:
    return [x.strip() for x in os.getenv(name, "").split(",") if x.strip()]

def load_settings() -> Settings:
    env = {
        "WATCHLIST_MODE": os.getenv("WATCHLIST_MODE", "TOP100").upper(),
        "MANUAL_SYMBOLS": [s.strip().upper() for s in os.getenv("MANUAL_SYMBOLS", "").split(",") if s.strip()],
        "TIMEFRAME": os.getenv("TIMEFRAME", "1h"),
        "TOP_N": int(os.getenv("TOP_N", "5")),
        "LANGUAGE": os.getenv("LANGUAGE", "LV").upper(),
        "SHORT_FORMAT": os.getenv("SHORT_FORMAT", "true").lower() == "true",
        "LONG_FORMAT": os.getenv("LONG_FORMAT", "false").lower() == "true",
        "DETAIL_EMOJI": os.getenv("DETAIL_EMOJI", "true").lower() == "true",
        "MIN_24H_VOLUME_USD": float(os.getenv("MIN_24H_VOLUME_USD", "50000000")),
        "MIN_24H_PCT": float(os.getenv("MIN_24H_PCT", "3.0")),
        "MA_PERIOD": int(os.getenv("MA_PERIOD", "20")),
        "RSI_THRESHOLD": float(os.getenv("RSI_THRESHOLD", "55")),
        "ATR_PCT_MIN": float(os.getenv("ATR_PCT_MIN", "1.5")),
        # TF dinamika
        "MIN_24H_VOLUME_USD_15M": _maybe_float("MIN_24H_VOLUME_USD_15M"),
        "MIN_24H_PCT_15M": _maybe_float("MIN_24H_PCT_15M"),
        "MA_PERIOD_15M": _maybe_int("MA_PERIOD_15M"),
        "RSI_THRESHOLD_15M": _maybe_float("RSI_THRESHOLD_15M"),
        "ATR_PCT_MIN_15M": _maybe_float("ATR_PCT_MIN_15M"),
        "MIN_24H_VOLUME_USD_1H": _maybe_float("MIN_24H_VOLUME_USD_1H"),
        "MIN_24H_PCT_1H": _maybe_float("MIN_24H_PCT_1H"),
        "MA_PERIOD_1H": _maybe_int("MA_PERIOD_1H"),
        "RSI_THRESHOLD_1H": _maybe_float("RSI_THRESHOLD_1H"),
        "ATR_PCT_MIN_1H": _maybe_float("ATR_PCT_MIN_1H"),
        "MIN_24H_VOLUME_USD_4H": _maybe_float("MIN_24H_VOLUME_USD_4H"),
        "MIN_24H_PCT_4H": _maybe_float("MIN_24H_PCT_4H"),
        "MA_PERIOD_4H": _maybe_int("MA_PERIOD_4H"),
        "RSI_THRESHOLD_4H": _maybe_float("RSI_THRESHOLD_4H"),
        "ATR_PCT_MIN_4H": _maybe_float("ATR_PCT_MIN_4H"),
        "ADVICE_ENABLED": os.getenv("ADVICE_ENABLED", "true").lower() == "true",
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        "TELEGRAM_CHAT_IDS": _env_list("TELEGRAM_CHAT_IDS"),
    }
    try:
        cfg = Settings(**env)
    except ValidationError as e:
        raise SystemExit(f"Config validation error: {e}")

    if not cfg.TELEGRAM_BOT_TOKEN:
        raise SystemExit("Config error: TELEGRAM_BOT_TOKEN is empty or missing.")
    if not cfg.TELEGRAM_CHAT_IDS:
        raise SystemExit("Config error: TELEGRAM_CHAT_IDS is empty or missing (comma-separated numeric IDs).")

    return cfg

def _maybe_float(name: str):
    v = os.getenv(name)
    return float(v) if v not in (None, "",) else None

def _maybe_int(name: str):
    v = os.getenv(name)
    return int(v) if v not in (None, "",) else None

def resolve_thresholds(cfg: Settings) -> Dict[str, float | int]:
    """Atgriež TF-konkrētus sliekšņus (ja nav iestatīti, krīt uz bāzi)."""
    tf = cfg.TIMEFRAME.lower()
    pick = lambda base, v15, v1h, v4h: (
        v15 if tf == "15m" and v15 is not None else
        v1h if tf == "1h"  and v1h is not None else
        v4h if tf == "4h"  and v4h is not None else
        base
    )
    return {
        "MIN_24H_VOLUME_USD": pick(cfg.MIN_24H_VOLUME_USD, cfg.MIN_24H_VOLUME_USD_15M, cfg.MIN_24H_VOLUME_USD_1H, cfg.MIN_24H_VOLUME_USD_4H),
        "MIN_24H_PCT": pick(cfg.MIN_24H_PCT, cfg.MIN_24H_PCT_15M, cfg.MIN_24H_PCT_1H, cfg.MIN_24H_PCT_4H),
        "MA_PERIOD": pick(cfg.MA_PERIOD, cfg.MA_PERIOD_15M, cfg.MA_PERIOD_1H, cfg.MA_PERIOD_4H),
        "RSI_THRESHOLD": pick(cfg.RSI_THRESHOLD, cfg.RSI_THRESHOLD_15M, cfg.RSI_THRESHOLD_1H, cfg.RSI_THRESHOLD_4H),
        "ATR_PCT_MIN": pick(cfg.ATR_PCT_MIN, cfg.ATR_PCT_MIN_15M, cfg.ATR_PCT_MIN_1H, cfg.ATR_PCT_MIN_4H),
    }
