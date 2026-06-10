"""
Main entry point for the Nigerian P2P Crypto Exchange Telegram Bot.

Architecture:
    - adapters/telegram_adapter.py  — Telegram-specific I/O (Update ↔ IncomingMessage)
    - engine.py                     — platform-agnostic conversation state machine
    - middleware/rate_limiter.py    — rate limiting / anti-spam
    - database.py                   — Supabase (persistence, sessions, bans, stats)
    - utils/tron_utils.py           — TRON blockchain (TronGrid)
    - utils/bank_utils.py           — NGN payment processing (Paystack stub)

This module is the glue: it creates the Telegram Application, instantiates the
engine and adapter, and registers handlers. All business logic lives in engine.py.
"""

import asyncio
import logging
import os
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import NoReturn

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes,
)

from engine import ConversationEngine
from adapters.telegram_adapter import TelegramAdapter
from database import (
    get_all_users, get_setting, set_setting,
    cleanup_stale_sessions,
)
from config import BOT_TOKEN, ADMIN_IDS

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Infrastructure: Health-check server
# ---------------------------------------------------------------------------


class _HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot Service Active")

    def log_message(self, format: str, *args) -> None:
        return  # silence


def _run_health_check_server() -> None:
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), _HealthCheckHandler)
        logger.info(f"Health-check server active on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health-check server: {e}")


# ---------------------------------------------------------------------------
# Application bootstrap (global references for handler callbacks)
# ---------------------------------------------------------------------------

_adapter: TelegramAdapter | None = None
_engine: ConversationEngine | None = None


# ---------------------------------------------------------------------------
# Telegram handler callbacks (thin — all logic in engine)
# ---------------------------------------------------------------------------

async def _on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any incoming Telegram message (text, photo, document)."""
    assert _adapter is not None and _engine is not None
    msg = _adapter.parse_update(update)
    if msg.user_id == 0:
        return
    response = _engine.handle_message(msg)
    await _adapter.send_response(msg.chat_id, response)


async def _on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin inline-button callbacks (approve/reject/resolve)."""
    assert _adapter is not None and _engine is not None
    query = update.callback_query
    await query.answer()

    if query.data.startswith("admin_"):
        admin_uid, action, tx_id, chat_id = _adapter.parse_callback(query)
        response = _engine.handle_admin_action(admin_uid, action, tx_id, chat_id)
        await _adapter.edit_message(chat_id, query.message.message_id, response)


async def _on_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin-only text commands: /setrate, /broadcast, /stats, /pending, /user, /ban, /unban, /resolve."""
    assert _adapter is not None and _engine is not None

    text = update.message.text.strip()
    parts = text.split(maxsplit=1)
    command = parts[0].lstrip("/")
    args = parts[1].split() if len(parts) > 1 else []

    # Broadcast is async over many users — handled separately
    if command == "broadcast":
        message = " ".join(args)
        if not message:
            await update.message.reply_text("Usage: /broadcast <message>")
            return
        users = get_all_users()
        sent_count, failed_count = 0, 0
        for user_id in users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 *Announcement*\n\n{message}",
                    parse_mode="Markdown",
                )
                sent_count += 1
                await asyncio.sleep(0.05)
            except TelegramError:
                failed_count += 1
        await update.message.reply_text(
            f"✅ Broadcast Status: {sent_count} Delivered | {failed_count} Blocked"
        )
        return

    response = _engine.handle_admin_command(update.effective_user.id, command, args)
    await update.message.reply_text(response.text, parse_mode=response.parse_mode)


async def _on_error(update, context) -> None:
    logger.error(f"Runtime Error: Update {update} triggered {context.error}")


# ---------------------------------------------------------------------------
# Background: periodic reminder scheduler (improved error handling)
# ---------------------------------------------------------------------------

async def _reminder_scheduler(app: Application) -> NoReturn:
    """
    Re-engage dormant users every 90 days.
    Tracks per-user consecutive failures to detect blocked/inactive users.
    """
    failure_counts: dict[int, int] = {}
    max_consecutive_failures = 3

    while True:
        last_date_str = get_setting("last_reminder_date")
        if not last_date_str:
            set_setting("last_reminder_date", datetime.now().strftime("%Y-%m-%d"))
        else:
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
            if (datetime.now() - last_date).days >= 90:
                logger.info("Dispatching periodic engagement reminder...")
                text = ConversationEngine.get_reminder_text()
                users = get_all_users()
                sent_count, fail_count = 0, 0

                for user_id in users:
                    try:
                        await app.bot.send_message(
                            chat_id=user_id, text=text, parse_mode="Markdown"
                        )
                        sent_count += 1
                        failure_counts.pop(user_id, None)  # reset on success
                        await asyncio.sleep(0.05)
                    except TelegramError as e:
                        fail_count += 1
                        failure_counts[user_id] = failure_counts.get(user_id, 0) + 1
                        logger.warning(
                            f"Reminder failed for {user_id} "
                            f"({failure_counts[user_id]} consecutive): {e}"
                        )
                        # Stop sending to users who consistently fail
                        if failure_counts[user_id] >= max_consecutive_failures:
                            logger.info(
                                f"Skipping user {user_id} for future reminders "
                                f"(blocked bot or deactivated account)"
                            )
                    except Exception as e:
                        fail_count += 1
                        logger.error(f"Unexpected reminder error for {user_id}: {e}")

                set_setting("last_reminder_date", datetime.now().strftime("%Y-%m-%d"))
                logger.info(
                    f"Reminder round complete: {sent_count} sent, {fail_count} failed, "
                    f"{len([v for v in failure_counts.values() if v >= max_consecutive_failures])} skipped"
                )

        await asyncio.sleep(86400)


async def _post_init(app: Application) -> None:
    """Called once after the bot application starts."""
    assert _engine is not None

    # Restore sessions from DB
    restored = _engine.restore_sessions()
    if restored:
        logger.info(f"Session recovery: {restored} conversations restored")

    # Clean up stale sessions
    cleaned = cleanup_stale_sessions(max_age_hours=24)
    if cleaned:
        logger.info(f"Session cleanup: {cleaned} stale sessions removed")

    # Start reminder scheduler
    asyncio.create_task(_reminder_scheduler(app))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    global _adapter, _engine

    from database import init_db
    init_db()

    # Start health-check server in background
    threading.Thread(target=_run_health_check_server, daemon=True).start()

    # Build Telegram application
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    # Create adapter and engine
    adapter = TelegramAdapter(app)

    async def notify_admin(chat_id, text, buttons=None, photo_url=""):
        await adapter.notify_admin(chat_id, text, buttons=buttons, photo_url=photo_url)

    async def notify_user(chat_id, text):
        await adapter.notify_user(chat_id, text)

    engine = ConversationEngine(
        notify_admin=notify_admin,
        notify_user=notify_user,
    )

    _adapter = adapter
    _engine = engine

    # ── Register handlers ──────────────────────────────────────────

    # Admin commands
    for cmd in ("setrate", "broadcast", "stats", "pending", "user", "ban", "unban", "resolve"):
        app.add_handler(CommandHandler(cmd, _on_admin_command), group=1)

    # Admin callbacks (inline buttons)
    app.add_handler(CallbackQueryHandler(_on_callback, pattern="^admin_"), group=1)

    # Catch-all: regular user messages
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND,
            _on_message,
        ),
        group=0,
    )

    app.add_error_handler(_on_error)

    logger.info("Nigerian P2P Crypto Exchange Bot initialized.")

    # Fix for Windows event loop issues
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"CRITICAL SYSTEM FAILURE: {e}", exc_info=True)
        sys.exit(1)
