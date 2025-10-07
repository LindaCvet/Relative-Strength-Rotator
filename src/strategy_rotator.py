import json
import os
from typing import Dict, List, Tuple, Optional
import pandas as pd

from .indicators import sma, rsi, atr_pct

def filter_and_rank(
    markets: List[Dict],
    symbol_to_product: Dict[str, str],
    ohlcv_fetcher,
    timeframe: str,
    ma_period: int,
    rsi_threshold: float,
    atr_pct_min: float,
    min_24h_volume_usd: float,
    min_24h_pct: float,
    top_n: int
) -> Tuple[List[Dict], List[Dict]]:
    """Returns (ranked_top, skipped)"""
    gran = {"15m": 900, "1h": 3600, "4h": 14400}[timeframe]
    candidates = []
    skipped = []

    for m in markets:
        sym = m.get("symbol", "").upper()
        name = m.get("name", sym)
        vol = float(m.get("total_volume", 0.0))
        # CoinGecko reports price_change_percentage_24h in key 'price_change_percentage_24h_in_currency' sometimes;
        pct = m.get("price_change_percentage_24h")
        if pct is None:
            pct = m.get("price_change_percentage_24h_in_currency")
        if pct is None:
            pct = 0.0
        pct = float(pct)

        # skip stablecoins by heuristic:
        if sym in {"USDT","USDC","DAI","TUSD","USDP","FDUSD","PYUSD"}:
            skipped.append({"symbol": sym, "reason": "stablecoin"})
            continue

        if vol < min_24h_volume_usd or pct < min_24h_pct:
            skipped.append({"symbol": sym, "reason": "volume/pct filter"})
            continue

        pid = symbol_to_product.get(sym)
        if not pid:
            skipped.append({"symbol": sym, "reason": "not_on_coinbase_usd"})
            continue

        df = ohlcv_fetcher(pid, gran, 300)
        if df is None or len(df) < max(ma_period, 50):
            skipped.append({"symbol": sym, "reason": "no_ohlcv"})
            continue

        df["ma"] = sma(df["close"], ma_period)
        df["rsi"] = rsi(df["close"], 14)
        df["atrpct"] = atr_pct(df, 14)

        last = df.iloc[-1]
        conds = {
            "price_above_ma": bool(last["close"] > last["ma"] if pd.notna(last["ma"]) else False),
            "rsi_ok": bool(last["rsi"] > rsi_threshold if pd.notna(last["rsi"]) else False),
            "atr_ok": bool(last["atrpct"] > atr_pct_min if pd.notna(last["atrpct"]) else False),
        }
        if not all(conds.values()):
            skipped.append({"symbol": sym, "reason": f"indicators fail {conds}"})
            continue

        score = (pct * 0.7) + (max(0.0, (last["rsi"] - rsi_threshold)) * 0.2) + (max(0.0, (last["atrpct"] - atr_pct_min)) * 0.1)
        candidates.append({
            "symbol": sym, "name": name, "product_id": pid,
            "pct24h": round(pct, 2),
            "volume_usd": float(vol),
            "price": float(last["close"]),
            "ma": float(last["ma"]) if pd.notna(last["ma"]) else None,
            "rsi": float(last["rsi"]) if pd.notna(last["rsi"]) else None,
            "atrpct": float(last["atrpct"]) if pd.notna(last["atrpct"]) else None,
            "score": float(score),
        })

    ranked = sorted(candidates, key=lambda x: x["score"], reverse=True)[:top_n]
    return ranked, skipped

def compute_entry_sl_tp(row: Dict, df: pd.DataFrame) -> Dict:
    """
    Heuristika (TF=1h):
      - entry: current close, ja cena virs MA un RSI>55; citādi "wait"
      - SL: entry - 1.5 * ATR (naudas vienībās)
      - TP1: entry + 1 * ATR, TP2: entry + 2 * ATR
      - Alternatīva TP: pēdējais swing high (≈ pēdējo 20 baru max)
    """
    last = df.iloc[-1]
    atr_val = (row["atrpct"] / 100.0) * last["close"]  # ATR in price units
    entry_ok = last["close"] > row["ma"] and row["rsi"] and row["rsi"] > 55
    advice = "GAIDĪT"
    if entry_ok:
        advice = "VAR PIRKT (momentum)"
    # Swings
    swing_high = df["high"].tail(20).max()
    swing_low = df["low"].tail(20).min()

    entry = float(last["close"])
    sl = float(entry - 1.5 * atr_val)
    tp1 = float(entry + 1.0 * atr_val)
    tp2 = float(max(entry + 2.0 * atr_val, swing_high))  # dod priekšroku swing high, ja augstāks

    # drošības noapaļošana
    return {
        "entry": round(entry, 6),
        "sl": round(sl, 6),
        "tp1": round(tp1, 6),
        "tp2": round(tp2, 6),
        "advice": advice
    }

def load_prev_top(state_file: str) -> List[str]:
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("top_symbols", [])
        except Exception:
            return []
    return []

def diff_labels(current_syms: List[str], prev_syms: List[str]) -> Dict[str, str]:
    labels = {}
    for s in current_syms:
        labels[s] = "KEEP" if s in prev_syms else "NEW"
    for s in prev_syms:
        if s not in labels:
            labels[s] = "DROP"
    return labels

def save_top(state_file: str, top_symbols: List[str]) -> bool:
    payload = {"top_symbols": top_symbols}
    old = load_prev_top(state_file)
    changed = old != top_symbols
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return changed
