from typing import List
from telegram import Bot
from telegram.constants import ParseMode
import time

def send_telegram_message(token: str, chat_ids: List[str], text: str):
    bot = Bot(token=token)
    for cid in chat_ids:
        bot.send_message(chat_id=cid, text=text)
        time.sleep(1.0)  # vienkāršs throttling
