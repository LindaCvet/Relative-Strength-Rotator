from datetime import datetime
import pytz

from src.config import load_settings, resolve_thresholds
from src.data_sources import get_top100_markets_coingecko, get_coinbase_products, pick_usd_pairs, fetch_coinbase_ohlcv, timeframe_to_granularity_seconds
from src.strategy_rotator import filter_and_rank, load_prev_top, diff_labels, save_top, compute_entry_sl_tp
from src.formatter import build_message_lv
from src.notifier import send_telegram_message

def main():
    cfg = load_settings()
    eff = resolve_thresholds(cfg)

    print(f"Using TF={cfg.TIMEFRAME}; effective thresholds: {eff}")

    # 1) CoinGecko Top-100
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
        ma_period=eff["MA_PERIOD"],
        rsi_threshold=eff["RSI_THRESHOLD"],
        atr_pct_min=eff["ATR_PCT_MIN"],
        min_24h_volume_usd=eff["MIN_24H_VOLUME_USD"],
        min_24h_pct=eff["MIN_24H_PCT"],
        top_n=cfg.TOP_N
    )

    # 4) Advice (optional)
    if cfg.ADVICE_ENABLED:
        for r in ranked:
            df = fetch_coinbase_ohlcv(cfg.COINBASE_BASE, r["product_id"], timeframe_to_granularity_seconds(cfg.TIMEFRAME), 300)
            if df is not None and len(df) > 50:
                r["advice"] = compute_entry_sl_tp(r, df)

    # 5) Labels & prev ranks
    prev_syms, prev_ranks = load_prev_top(cfg.STATE_FILE)
    cur_syms = [r["symbol"] for r in ranked]
    labels = diff_labels(cur_syms, prev_syms)
    changed = save_top(cfg.STATE_FILE, ranked)

    # 6) Build message
    now_riga = datetime.now(pytz.timezone("Europe/Riga"))
    text = build_message_lv(
        now_riga=now_riga,
        timeframe=cfg.TIMEFRAME,
        top_rows=ranked,
        labels=labels,
        short_format=cfg.SHORT_FORMAT,
        include_advice=cfg.ADVICE_ENABLED,
        detail_emoji=cfg.DETAIL_EMOJI,
        long_format=cfg.LONG_FORMAT,
        prev_ranks=prev_ranks
    )

    print(f"Found {len(cfg.TELEGRAM_CHAT_IDS)} Telegram chat IDs.")
    # 7) Send
    send_telegram_message(cfg.TELEGRAM_BOT_TOKEN, cfg.TELEGRAM_CHAT_IDS, text)

    # 8) Summary
    print("\n=== SUMMARY ===")
    print(text)
    print("\nSkipped count:", len(skipped))

if __name__ == "__main__":
    main()
