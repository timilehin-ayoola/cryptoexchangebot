"""
Platform adapters for the P2P Crypto Exchange Bot.

Each adapter translates between a specific messaging platform's API and the
platform-agnostic engine.

Currently supported:
    - Telegram  (adapters.telegram_adapter)

To add a new platform:
    1. Create adapters/<platform>_adapter.py
    2. Implement parse_<event>() → IncomingMessage
    3. Implement send_response(chat_id, BotResponse)
    4. Implement notify_admin() and notify_user()
    5. Wire handlers in bot.py or a platform-specific entry point
"""

__all__ = [
    "TelegramAdapter",
]

from adapters.telegram_adapter import TelegramAdapter
