import time
import pandas as pd
from typing import List, Dict, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

COINGECKO_MARKETS = "/coins/markets"
COINBASE_PRODUCTS = "/products"
COINBASE_CANDLES = "/products/{product_id}/candles"

class RateLimitError(Exception):
    pass

def timeframe_to_granularity_seconds(tf: str) -> int:
    tf = tf.lower()
    return {"15m": 900, "1h": 3600, "4h": 14400}.get(tf, 3600)

@retry(reraise=True, stop=stop_after_attempt(4),
       wait=wait_exponential(multiplier=1, min=1, max=8),
       retry=retry_if_exception_type((httpx.ReadTimeout, httpx.ConnectError, RateLimitError)))
def _get(client: httpx.Client, url: str, params: dict = None, headers: dict = None):
    r = client.get(url, params=params, headers=headers, timeout=30)
    if r.status_code == 429:
        raise RateLimitError("429 from API")
    r.raise_for_status()
    return r.json()

def get_top100_markets_coingecko(base_url: str) -> List[Dict]:
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "price_change_percentage": "24h",
        "sparkline": "false",
    }
    with httpx.Client() as client:
        data = _get(client, base_url + COINGECKO_MARKETS, params=params)
    return data

def get_coinbase_products(base_url: str) -> List[Dict]:
    with httpx.Client() as client:
        data = _get(client, base_url + COINBASE_PRODUCTS)
    return data

def pick_usd_pairs(products: List[Dict]) -> Dict[str, str]:
    """Map SYMBOL -> PRODUCT_ID where quote is USD (e.g., ETH -> ETH-USD)."""
    out = {}
    for p in products:
        pid = p.get("id")  # e.g., ETH-USD
        if not pid or not pid.endswith("-USD"): 
            continue
        base = pid.split("-")[0].upper()
        out[base] = pid
    return out

def fetch_coinbase_ohlcv(base_url: str, product_id: str, granularity_s: int, limit: int = 300) -> Optional[pd.DataFrame]:
    """
    Coinbase candles response rows:
    [ time, low, high, open, close, volume ] in reverse chronological order.
    """
    params = {"granularity": granularity_s}
    url = base_url + COINBASE_CANDLES.format(product_id=product_id)
    with httpx.Client() as client:
        data = _get(client, url, params=params)
    if not data:
        return None
    # Reverse to chronological
    data = list(reversed(data))
    df = pd.DataFrame(data, columns=["time", "low", "high", "open", "close", "volume"])
    if len(df) > limit:
        df = df.iloc[-limit:]
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df
