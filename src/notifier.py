from typing import List
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter, TimedOut, NetworkError
import time
import traceback

def send_telegram_message(token: str, chat_ids: List[str], text: str):
    bot = Bot(token=token)
    for cid in chat_ids:
        tries = 0
        while True:
            tries += 1
            try:
                bot.send_message(chat_id=cid, text=text, disable_web_page_preview=True)
                print(f"[telegram] sent to {cid}")
                time.sleep(1.0)  # vienkāršs throttling
                break
            except RetryAfter as e:
                wait_s = int(getattr(e, "retry_after", 5)) + 1
                print(f"[telegram] RetryAfter for {cid}: waiting {wait_s}s …")
                time.sleep(wait_s)
            except (TimedOut, NetworkError) as e:
                if tries <= 3:
                    print(f"[telegram] Network error for {cid}: {e}; retrying …")
                    time.sleep(2)
                else:
                    print(f"[telegram] Network error (giving up) for {cid}: {e}")
                    break
            except TelegramError as e:
                # Izdrukājam visu, ko varam (ļoti noder kanāliem/atļaujām)
                print(f"[telegram] TelegramError for {cid}: {e}")
                tb = traceback.format_exc()
                print(tb)
                # pēc šādas kļūdas parasti nav jēga atkārtot
                break
            except Exception as e:
                print(f"[telegram] Unexpected error for {cid}: {e}")
                print(traceback.format_exc())
                break
