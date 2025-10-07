from datetime import datetime
from typing import List, Dict, Optional

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
    include_advice: bool,
    detail_emoji: bool,
    long_format: bool,
    prev_ranks: Optional[Dict[str, int]] = None
) -> str:
    header = f"Relative Strength Rotator — {now_riga.strftime('%H:%M')} Rīga (TF: {timeframe})"
    lines = [header, "Top 5:"]

    if not top_rows:
        lines.append("• Šoreiz kandidātu nav (iespējams, pārāk stingri filtri vai tirgus bez momentuma).")
    else:
        for i, r in enumerate(top_rows, 1):
            lab = labels.get(r["symbol"], "")
            lab_str = f" [{lab}]" if lab in {"NEW","KEEP"} else ""
            arrow = r.get("arrow", "")
            if not detail_emoji:
                arrow = ""
            ma = r.get("ma")
            rsi = r.get("rsi")
            base = (
                f"{i}) {r['symbol']} {arrow}  {r['pct24h']:+.1f}% "
                f"(Vol {fmt_usd(r['volume_usd'])})  MA{int(ma) if ma else '?'}  RSI {int(rsi) if rsi else '?'}"
                f"{lab_str}"
            )
            # Garajā formātā pievienojam ranga izmaiņu
            if long_format and prev_ranks:
                prev = prev_ranks.get(r["symbol"])
                if prev is not None:
                    delta = prev - i
                    if   delta > 0: ch = f" ↑{delta}"
                    elif delta < 0: ch = f" ↓{abs(delta)}"
                    else:           ch = " ="
                    base += f"  (rangs: {prev}→{i}{ch})"
                else:
                    base += "  (jauns ienācējs)"
            lines.append(base)

    if include_advice and top_rows:
        lines.append("")
        lines.append("Ieteikumi (1h):")
        for r in top_rows:
            adv = r.get("advice", {})
            if adv:
                lines.append(f"• {r['symbol']}: entry {adv['entry']}, SL {adv['sl']}, TP1 {adv['tp1']}, TP2 {adv['tp2']} — {adv['advice']}")

    if long_format and prev_ranks:
        drops = [s for s, lab in labels.items() if lab == "DROP"]
        if drops:
            lines.append("")
            lines.append("Dropped iepriekš no Top 5:")
            lines.append("• " + ", ".join(drops))

    lines.append("")
    lines.append("Komentāri:")
    lines.append("• Top atlasīts pēc 24h momentuma, likviditātes un virs MA/RSI/ATR sliekšņiem.")
    lines.append("• Šī nav finanšu konsultācija. Izmanto savus risku parametrus.")
    return "\n".join(lines)
