# Relative Strength Rotator (GitHub-only)

Atlasām 1h momentum **Top 5** no CoinGecko Top-100, filtrējam pēc:
- 24h apjoms ≥ $50M
- 24h % izmaiņa ≥ +3%
- Cena > MA20 (1h)
- RSI > 55 (1h)
- ATR% (14, 1h) > 1.5

OHLCV no **Coinbase** (USD pāri).

## Rezultāts
Telegram ziņa (LV, īsais formāts) ar Top 5 un (pēc izvēles) ieteikumiem `entry/SL/TP` (heuristika no 1h ATR un swingiem).

## Konfigurācija
Env (GitHub Actions `env` vai Repo Secrets):
- `TELEGRAM_BOT_TOKEN` (secret)
- `TELEGRAM_CHAT_IDS` (secret) — komatu saraksts: `-1001234,1234567`
- `ADVICE_ENABLED` = `true|false`
- `TIMEFRAME` = `1h|4h|15m`
- u.c. (skat. `src/config.py`)

## Grafiks
Noklusēti 5×/dienā (UTC: 04:00, 08:00, 12:00, 16:00, 20:00).

## State
`last_top.json` tiek atjaunināts un ielikts commit, lai varētu izveidot `KEEP/NEW/DROP` loģiku.

## Brīdinājums
Šī nav finanšu konsultācija. Izmanto savu risku pārvaldību.
