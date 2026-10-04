"""
Telegram userbot: auto-replies to incoming private messages from your own account.

Setup:
  1. pip install telethon
  2. Get api_id/api_hash at https://my.telegram.org (log in with your own number)
  3. Set them below or via env vars TG_API_ID / TG_API_HASH
  4. Run: python telegram_autoreply.py
     First run asks for your phone number and the login code Telegram sends you —
     enter them yourself in the terminal. After that a session file is saved
     (telegram_session.session) so you won't need to log in again.

Customize AUTO_REPLY_TEXT and KEYWORD_REPLIES below.
"""

import os
from telethon import TelegramClient, events

API_ID = int(os.environ.get("TG_API_ID", "0"))
API_HASH = os.environ.get("TG_API_HASH", "")
SESSION_NAME = "telegram_session"

AUTO_REPLY_TEXT = "Привет! Сейчас не у телефона, отвечу позже."

# Optional: different replies for messages containing certain keywords (case-insensitive)
KEYWORD_REPLIES = {
    "срочно": "Вижу, что срочно — отвечу как можно скорее.",
}

# Only auto-reply once per chat per this many seconds, to avoid spamming
COOLDOWN_SECONDS = 3600
_last_replied = {}

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_new_message(event):
    import time

    chat_id = event.chat_id
    now = time.time()
    if now - _last_replied.get(chat_id, 0) < COOLDOWN_SECONDS:
        return

    text = (event.raw_text or "").lower()
    reply = AUTO_REPLY_TEXT
    for keyword, custom_reply in KEYWORD_REPLIES.items():
        if keyword.lower() in text:
            reply = custom_reply
            break

    await event.reply(reply)
    _last_replied[chat_id] = now
    print(f"Replied to chat {chat_id}")


def main():
    if not API_ID or not API_HASH:
        raise SystemExit("Set TG_API_ID and TG_API_HASH (env vars or in this file).")
    print("Starting... first run will ask for your phone number and login code.")
    client.start()
    print("Logged in. Listening for messages (Ctrl+C to stop).")
    client.run_until_disconnected()


if __name__ == "__main__":
    main()
