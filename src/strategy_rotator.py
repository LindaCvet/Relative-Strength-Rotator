import json
import os
from typing import Dict, List, Tuple, Optional
import pandas as pd

from .indicators import sma, rsi, atr_pct

STABLES = {"USDT","USDC","DAI","TUSD","USDP","FDUSD","PYUSD"}

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
    candidates, skipped = [], []

    for m in markets:
        sym = m.get("symbol", "").upper()
        name = m.get("name", sym)
        vol = float(m.get("total_volume", 0.0))
        pct = m.get("price_change_percentage_24h")
        if pct is None:
            pct = m.get("price_change_percentage_24h_in_currency", 0.0)
        pct = float(pct or 0.0)

        if sym in STABLES:
            skipped.append({"symbol": sym, "reason": "stablecoin"}); continue
        if vol < min_24h_volume_usd or pct < min_24h_pct:
            skipped.append({"symbol": sym, "reason": "volume/pct filter"}); continue

        pid = symbol_to_product.get(sym)
        if not pid:
            skipped.append({"symbol": sym, "reason": "not_on_coinbase_usd"}); continue

        df = ohlcv_fetcher(pid, gran, 300)
        if df is None or len(df) < max(ma_period, 50):
            skipped.append({"symbol": sym, "reason": "no_ohlcv"}); continue

        df["ma"] = sma(df["close"], ma_period)
        df["rsi"] = rsi(df["close"], 14)
        df["atrpct"] = atr_pct(df, 14)

        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else last
        arrow = "↑" if last["close"] > prev["close"] else ("↓" if last["close"] < prev["close"] else "=")

        conds = {
            "price_above_ma": bool(last["close"] > last["ma"] if pd.notna(last["ma"]) else False),
            "rsi_ok": bool(last["rsi"] > rsi_threshold if pd.notna(last["rsi"]) else False),
            "atr_ok": bool(last["atrpct"] > atr_pct_min if pd.notna(last["atrpct"]) else False),
        }
        if not all(conds.values()):
            skipped.append({"symbol": sym, "reason": f"indicators fail {conds}"}); continue

        score = (pct * 0.7) + max(0.0, (last["rsi"] - rsi_threshold)) * 0.2 + max(0.0, (last["atrpct"] - atr_pct_min)) * 0.1
        candidates.append({
            "symbol": sym, "name": name, "product_id": pid,
            "pct24h": round(pct, 2),
            "volume_usd": float(vol),
            "price": float(last["close"]),
            "ma": float(last["ma"]) if pd.notna(last["ma"]) else None,
            "rsi": float(last["rsi"]) if pd.notna(last["rsi"]) else None,
            "atrpct": float(last["atrpct"]) if pd.notna(last["atrpct"]) else None,
            "arrow": arrow,
            "score": float(score),
        })

    ranked = sorted(candidates, key=lambda x: x["score"], reverse=True)[:top_n]
    return ranked, skipped

def compute_entry_sl_tp(row: Dict, df: pd.DataFrame) -> Dict:
    last = df.iloc[-1]
    atr_val = (row["atrpct"] / 100.0) * last["close"]  # ATR price units
    entry_ok = last["close"] > row["ma"] and row.get("rsi", 0) > 55
    advice = "GAIDĪT"
    if entry_ok:
        advice = "VAR PIRKT (momentum)"
    swing_high = df["high"].tail(20).max()
    entry = float(last["close"])
    sl = float(entry - 1.5 * atr_val)
    tp1 = float(entry + 1.0 * atr_val)
    tp2 = float(max(entry + 2.0 * atr_val, swing_high))
    return {
        "entry": round(entry, 6),
        "sl": round(sl, 6),
        "tp1": round(tp1, 6),
        "tp2": round(tp2, 6),
        "advice": advice
    }

# ── State ar rangu ─────────────────────────────────────────────────────────────

def load_prev_top(state_file: str) -> Tuple[List[str], Dict[str, int]]:
    """
    Atbalsta veco formātu {"top_symbols": [...]} un jauno:
    {"top": [{"symbol":"ETH","rank":1},...], "ts":"..."}
    """
    if not os.path.exists(state_file):
        return [], {}
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return [], {}

    # jauns formāts
    if "top" in data and isinstance(data["top"], list):
        syms = [it["symbol"] for it in data["top"]]
        ranks = {it["symbol"]: int(it.get("rank", i+1)) for i, it in enumerate(data["top"])}
        return syms, ranks

    # vecais formāts
    syms = data.get("top_symbols", [])
    ranks = {s: i+1 for i, s in enumerate(syms)}
    return syms, ranks

def diff_labels(current_syms: List[str], prev_syms: List[str]) -> Dict[str, str]:
    labels = {}
    for s in current_syms:
        labels[s] = "KEEP" if s in prev_syms else "NEW"
    for s in prev_syms:
        if s not in labels:
            labels[s] = "DROP"
    return labels

def save_top(state_file: str, ranked: List[Dict]) -> bool:
    top_payload = [{"symbol": r["symbol"], "rank": i+1} for i, r in enumerate(ranked)]
    payload = {"top": top_payload}
    old_syms, _ = load_prev_top(state_file)
    new_syms = [r["symbol"] for r in ranked]
    changed = old_syms != new_syms
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return changed
