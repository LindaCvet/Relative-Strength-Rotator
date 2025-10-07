import json
from datetime import datetime
import pytz
import pandas as pd

from src.config import load_settings
from src.data_sources import get_top100_markets_coingecko, get_coinbase_products, pick_usd_pairs, fetch_coinbase_ohlcv, timeframe_to_granularity_seconds
from src.strategy_rotator import filter_and_rank, load_prev_top, diff_labels, save_top, compute_entry_sl_tp
from src.formatter import build_message_lv
from src.notifier import send_telegram_message

def main():
    cfg = load_settings()
    # Redzamībā: cik čatu?
    print(f"Found {len(cfg.TELEGRAM_CHAT_IDS)} Telegram chat IDs.")

    # 1) Pull CoinGecko Top-100
    markets = get_top100_markets_coingecko(cfg.COINGECKO_BASE)

    # 2) Coinbase USD pairs
    products = get_coinbase_products(cfg.COINBASE_BASE)
    symbol_to_product = pick_usd_pairs(products)

    # 3) Filter & Rank
    ranked, skipped = filter_and_rank(
        markets=markets,
        symbol_to_product=symbol_to_product,
        ohlcv_fetcher=lambda pid, gran, lim: fetch_coinbase_ohlcv(cfg.COINBASE_BASE, pid, gran, lim),
        timeframe=cfg.TIMEFRAME,
        ma_period=cfg.MA_PERIOD,
        rsi_threshold=cfg.RSI_THRESHOLD,
        atr_pct_min=cfg.ATR_PCT_MIN,
        min_24h_volume_usd=cfg.MIN_24H_VOLUME_USD,
        min_24h_pct=cfg.MIN_24H_PCT,
        top_n=cfg.TOP_N
    )

    # 4) Advice (optional)
    if cfg.ADVICE_ENABLED:
        for r in ranked:
            df = fetch_coinbase_ohlcv(cfg.COINBASE_BASE, r["product_id"], timeframe_to_granularity_seconds(cfg.TIMEFRAME), 300)
            if df is not None and len(df) > 50:
                r["advice"] = compute_entry_sl_tp(r, df)

    # 5) Labels (KEEP/NEW/DROP) from last run (state file committed in repo)
    prev_syms = load_prev_top(cfg.STATE_FILE)
    cur_syms = [r["symbol"] for r in ranked]
    labels = diff_labels(cur_syms, prev_syms)
    changed = save_top(cfg.STATE_FILE, cur_syms)

    # 6) Build message (LV short format, with optional advice lines)
    now_riga = datetime.now(pytz.timezone("Europe/Riga"))
    text = build_message_lv(
        now_riga=now_riga,
        timeframe=cfg.TIMEFRAME,
        top_rows=ranked,
        labels=labels,
        short_format=cfg.SHORT_FORMAT,
        include_advice=cfg.ADVICE_ENABLED
    )

    # 7) Send to Telegram
    send_telegram_message(cfg.TELEGRAM_BOT_TOKEN, cfg.TELEGRAM_CHAT_IDS, text)

    # 8) Print GitHub summary/log
    print("\n=== SUMMARY ===")
    print(text)
    print("\nSkipped count:", len(skipped))

if __name__ == "__main__":
    main()
