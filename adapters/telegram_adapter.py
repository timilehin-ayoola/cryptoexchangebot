"""
Telegram adapter — bridges python-telegram-bot types to the platform-agnostic engine.

This module contains ALL Telegram-specific imports. When adding WhatsApp, create
a separate adapters/whatsapp_adapter.py with no Telegram imports here.
"""

from __future__ import annotations

import logging
from typing import Callable, Awaitable

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler,
)
from telegram.error import TelegramError

from schema_types import IncomingMessage, BotResponse, Button, AttachmentType
from engine import ConversationEngine
from database import get_all_users
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Sentinel — kept for ConversationHandler compatibility, but unused by engine
TELEGRAM_DONE = ConversationHandler.END


class TelegramAdapter:
    """
    Translates between Telegram's Update/Context types and our engine's
    IncomingMessage / BotResponse types.
    """

    def __init__(self, app: Application):
        self._app = app

    # ------------------------------------------------------------------
    # Incoming: Telegram → engine
    # ------------------------------------------------------------------

    def parse_update(self, update: Update) -> IncomingMessage:
        """Convert a Telegram Update into a platform-agnostic IncomingMessage."""
        msg = update.message
        if msg is None:
            # E.g. an edited message — skip
            return IncomingMessage(user_id=0, chat_id=0)

        # Extract attachments
        attachments = []
        if msg.photo:
            attachments.append(Attachment(
                type=AttachmentType.PHOTO,
                file_id=msg.photo[-1].file_id,
            ))
        if msg.document:
            attachments.append(Attachment(
                type=AttachmentType.DOCUMENT,
                file_id=msg.document.file_id,
            ))

        return IncomingMessage(
            user_id=msg.from_user.id,
            chat_id=msg.chat_id,
            text=msg.text or msg.caption or "",
            attachments=attachments,
            platform="telegram",
            raw=update,
        )

    def parse_callback(self, query: CallbackQuery) -> tuple[int, str, int, str | int]:
        """
        Extract (admin_user_id, action, tx_id, chat_id) from a callback query.
        """
        parts = query.data.split("_")
        action = parts[1]
        tx_id = int(parts[2])
        admin_user_id = query.from_user.id
        chat_id = query.message.chat_id
        return admin_user_id, action, tx_id, chat_id

    # ------------------------------------------------------------------
    # Outgoing: engine → Telegram
    # ------------------------------------------------------------------

    async def send_response(
        self, chat_id: str | int, response: BotResponse
    ) -> None:
        """Send a BotResponse through the Telegram Bot API."""
        markup = self._build_markup(response.buttons)

        try:
            if response.photo_url:
                await self._app.bot.send_photo(
                    chat_id=chat_id,
                    photo=response.photo_url,
                    caption=response.text,
                    parse_mode=response.parse_mode,
                    reply_markup=markup,
                )
            elif response.document_path:
                await self._app.bot.send_document(
                    chat_id=chat_id,
                    document=response.document_path,
                    caption=response.text,
                    parse_mode=response.parse_mode,
                    reply_markup=markup,
                )
            else:
                await self._app.bot.send_message(
                    chat_id=chat_id,
                    text=response.text,
                    parse_mode=response.parse_mode,
                    reply_markup=markup,
                )
        except TelegramError as e:
            logger.error(f"Telegram send error to {chat_id}: {e}")

    async def edit_message(
        self, chat_id: str | int, message_id: int, response: BotResponse
    ) -> None:
        """Edit an existing message (e.g. after admin approval)."""
        markup = self._build_markup(response.buttons)
        try:
            await self._app.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=response.text,
                reply_markup=markup,
            )
        except TelegramError as e:
            logger.error(f"Telegram edit error on {chat_id}/{message_id}: {e}")

    # ------------------------------------------------------------------
    # Admin notifications (used by engine callbacks)
    # ------------------------------------------------------------------

    async def notify_admin(
        self,
        chat_id: str | int,
        text: str,
        buttons: list[list[Button]] | None = None,
        photo_url: str = "",
    ) -> None:
        """Send a message to an admin channel/user."""
        markup = self._build_markup(buttons)
        try:
            if photo_url:
                await self._app.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_url,
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=markup,
                )
            else:
                await self._app.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=markup,
                )
        except TelegramError as e:
            logger.error(f"Admin notification error to {chat_id}: {e}")

    async def notify_user(self, chat_id: str | int, text: str) -> None:
        """Send a message to a regular user."""
        await self.send_response(chat_id, BotResponse(text=text))

    # ------------------------------------------------------------------
    # Internal markup builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_markup(
        buttons: list[list[Button]] | None,
    ) -> InlineKeyboardMarkup | None:
        if not buttons:
            return None
        rows = []
        for row in buttons:
            btn_row = []
            for b in row:
                if b.url:
                    btn_row.append(InlineKeyboardButton(b.label, url=b.url))
                else:
                    btn_row.append(InlineKeyboardButton(b.label, callback_data=b.callback_data))
            rows.append(btn_row)
        return InlineKeyboardMarkup(rows)
