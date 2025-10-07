# src/formatter.py
from datetime import datetime
from typing import List, Dict

def fmt_usd(n: float) -> str:
    if n >= 1_000_000_000:
        return f"${n/1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n/1_000:.1f}K"
    return f"${n:.0f}"

def build_message_lv(
    now_riga: datetime,
    timeframe: str,
    top_rows: List[Dict],
    labels: Dict[str, str],
    short_format: bool,
    include_advice: bool
) -> str:
    header = f"Relative Strength Rotator — {now_riga.strftime('%H:%M')} Rīga (TF: {timeframe})"
    lines = [header, "Top 5:"]

    if not top_rows:
        lines.append("• Šoreiz kandidātu nav (iespējams, pārāk stingri filtri vai tirgus bez momentuma).")
    else:
        for i, r in enumerate(top_rows, 1):
            lab = labels.get(r["symbol"], "")
            lab_str = f"  [{lab}]" if lab in {"NEW","KEEP"} else ""
            base = (
                f"{i}) {r['symbol']}  {r['pct24h']:+.1f}% (24h Vol {fmt_usd(r['volume_usd'])})  "
                f"Cena>MA{lab_str}  RSI {int(r['rsi']) if r.get('rsi') else '?'}  ATR% {r['atrpct']:.1f}"
            )
            lines.append(base)

    if include_advice and top_rows:
        lines.append("")
        lines.append("Ieteikumi (1h):")
        for r in top_rows:
            adv = r.get("advice", {})
            if adv:
                lines.append(f"• {r['symbol']}: entry {adv['entry']}, SL {adv['sl']}, TP1 {adv['tp1']}, TP2 {adv['tp2']} — {adv['advice']}")

    lines.append("")
    lines.append("Komentāri:")
    lines.append("• Top atlasīts pēc 24h momentuma, likviditātes un virs MA/RSI/ATR sliekšņiem.")
    lines.append("• Šī nav finanšu konsultācija. Izmanto savus risku parametrus.")
    return "\n".join(lines)
