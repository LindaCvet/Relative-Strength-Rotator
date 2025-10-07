# src/notifier.py
from typing import List
import time
import httpx
import json

API_BASE = "https://api.telegram.org"

def send_telegram_message(token: str, chat_ids: List[str], text: str):
    """
    Sūta ziņu ar tiešo Telegram HTTP API (bez async, droši GitHub Actions).
    Ar vienkāršu throttling un kļūdu izdrukām.
    """
    if not chat_ids:
        print("[telegram] No chat IDs provided")
        return

    with httpx.Client(timeout=30.0) as client:
        for cid in chat_ids:
            cid = cid.strip()
            try:
                resp = client.post(
                    f"{API_BASE}/bot{token}/sendMessage",
                    data={
                        "chat_id": cid,
                        "text": text,
                        "disable_web_page_preview": "true",
                    },
                )
                try:
                    payload = resp.json()
                except Exception:
                    payload = {"raw": resp.text}

                if resp.status_code != 200 or not payload.get("ok", False):
                    print(f"[telegram] ERROR sending to {cid}: HTTP {resp.status_code} payload={payload}")
                else:
                    print(f"[telegram] sent to {cid}")
            except Exception as e:
                print(f"[telegram] Exception sending to {cid}: {e}")

            time.sleep(1.0)  # vienkāršs throttling
