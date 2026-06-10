"""
Platform-agnostic conversation engine for the P2P Crypto Exchange Bot.

Manages multi-step buy/sell flows as a pure state machine. No platform-specific
code here — all I/O goes through the IncomingMessage / BotResponse types.

Middleware integrated:
    - Rate limiting (anti-spam)
    - Ban checking
    - Session persistence (DB-backed, survives restarts)
    - Input validation hardening
    - Admin command expansion
"""

from __future__ import annotations

import logging
import re
from typing import Callable, Optional

from schema_types import (
    IncomingMessage, BotResponse, Button, AttachmentType,
    ConversationState,
)
from database import (
    auto_create_user, get_user, get_setting, set_setting,
    add_transaction, update_transaction_status, get_transaction,
    get_user_transactions, get_all_users,
    save_session, load_session, delete_session, load_all_sessions,
    cleanup_stale_sessions,
    ban_user, unban_user, is_banned, get_banned_users,
    get_pending_transactions, get_user_count, get_transaction_stats,
)
from config import (
    ADMIN_IDS, YOUR_BANK_NAME, YOUR_BANK_ACCOUNT,
    YOUR_BANK_ACCOUNT_NAME, YOUR_USDT_WALLET,
)
from responses import get_text
from middleware.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Trade bounds
MIN_TRADE_USDT: float = 1.0
MAX_TRADE_USDT: float = 10_000.0
MAX_PENDING_PER_USER: int = 3

# TRC20 address: starts with T, 34 chars, base58 alphabet
TRC20_REGEX = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")

# TRON tx hash: 64 hex characters
TX_HASH_REGEX = re.compile(r"^[a-fA-F0-9]{64}$")

# Conversation states
(
    BUY_AMOUNT, BUY_WALLET, BUY_CONFIRM_WALLET, BUY_PAYMENT_PROOF,
    SELL_AMOUNT, SELL_BANK_DETAILS, SELL_CONFIRM_ACC, SELL_TX_HASH,
) = range(8)

STATE_NAMES = {
    BUY_AMOUNT: "BUY_AMOUNT",
    BUY_WALLET: "BUY_WALLET",
    BUY_CONFIRM_WALLET: "BUY_CONFIRM_WALLET",
    BUY_PAYMENT_PROOF: "BUY_PAYMENT_PROOF",
    SELL_AMOUNT: "SELL_AMOUNT",
    SELL_BANK_DETAILS: "SELL_BANK_DETAILS",
    SELL_CONFIRM_ACC: "SELL_CONFIRM_ACC",
    SELL_TX_HASH: "SELL_TX_HASH",
}


# ---------------------------------------------------------------------------
# Conversation Engine
# ---------------------------------------------------------------------------

class ConversationEngine:
    """
    Stateful conversation manager with rate limiting, session persistence,
    and input validation.

    Args:
        notify_admin:  async callable(chat_id, text, buttons=None, photo_url="")
        notify_user:   async callable(chat_id, text)
    """

    def __init__(
        self,
        notify_admin: Callable,
        notify_user: Callable,
    ):
        self._sessions: dict[int, ConversationState] = {}
        self._notify_admin = notify_admin
        self._notify_user = notify_user
        self._rate_limiter = RateLimiter(
            max_requests=5,
            window_seconds=30,
            block_seconds=60,
        )

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    def _session(self, user_id: int) -> Optional[ConversationState]:
        return self._sessions.get(user_id)

    def _new_session(self, user_id: int, flow: str) -> ConversationState:
        s = ConversationState(state=0, flow=flow)
        self._sessions[user_id] = s
        return s

    def _end_session(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)
        delete_session(user_id)

    def _in_flow(self, user_id: int) -> bool:
        return user_id in self._sessions

    def _persist_session(self, user_id: int) -> None:
        """Save current session state to DB."""
        s = self._session(user_id)
        if s:
            save_session(user_id, s.flow, s.state, s.data)

    def restore_sessions(self) -> int:
        """Load sessions from DB on startup. Returns count restored."""
        sessions = load_all_sessions()
        restored = 0
        for row in sessions:
            uid = row["user_id"]
            flow = row.get("flow", "")
            state = row.get("state", 0)
            data = row.get("data", {})
            if flow and isinstance(data, dict):
                s = ConversationState(state=state, flow=flow, data=data)
                self._sessions[uid] = s
                restored += 1
        if restored:
            logger.info(f"Restored {restored} active sessions from DB")
        return restored

    # ------------------------------------------------------------------
    # Public entry — every incoming message lands here
    # ------------------------------------------------------------------

    def handle_message(self, msg: IncomingMessage) -> BotResponse:
        """Route a message through middleware then to the correct handler."""
        # Ensure user exists in DB
        auto_create_user(msg.user_id)

        # ── Rate limiting ───────────────────────────────────────────
        if not self._rate_limiter.is_allowed(msg.user_id):
            return BotResponse(
                text="⏳ You're sending too many requests. Please wait a moment and try again."
            )

        # ── Ban check ───────────────────────────────────────────────
        if is_banned(msg.user_id):
            return BotResponse(
                text="🚫 Your account has been restricted. Contact support for help."
            )

        # ── Ensure pending count within limits ─────────────────────
        session = self._session(msg.user_id)
        if session is None:
            pending = self._count_user_pending(msg.user_id)
            if pending >= MAX_PENDING_PER_USER:
                return BotResponse(
                    text=(
                        f"⚠️ You have {pending} pending orders. "
                        f"Please wait for them to be resolved before starting a new trade."
                    )
                )

        # ── Global commands (work even mid-flow) ────────────────────
        text_clean = msg.text.strip().lower()
        if text_clean in ("/cancel", "cancel"):
            self._end_session(msg.user_id)
            self._rate_limiter.reset(msg.user_id)
            return BotResponse(text=get_text("CANCEL_TRADE"))

        # ── Active conversation ─────────────────────────────────────
        if session is not None:
            return self._handle_conversation(msg, session)

        # ── Commands / top-level intents ────────────────────────────
        text = text_clean

        if text in ("/start", "hi", "hello"):
            return self._cmd_start()

        if text in ("/rates", "rate", "price", "rates"):
            return self._cmd_rates()

        if text in ("/buy", "buy"):
            return self._cmd_buy_start(msg.user_id)

        if text in ("/sell", "sell"):
            return self._cmd_sell_start(msg.user_id)

        if text in ("/history", "history", "order", "transaction"):
            return self._cmd_history(msg.user_id)

        if text in ("/support", "support", "help", "admin"):
            return self._cmd_support()

        if text == "/setrate":
            return BotResponse(text="Usage: `/setrate <buy_price> <sell_price>`")

        if text == "/broadcast":
            return BotResponse(text="Usage: `/broadcast <message>`")

        # Default: show welcome
        return self._cmd_start()

    def _count_user_pending(self, user_id: int) -> int:
        """Count pending transactions for a user."""
        txs = get_user_transactions(user_id, limit=20)
        return sum(1 for tx in txs if tx.get("status") == "pending")

    # ------------------------------------------------------------------
    # Top-level command handlers
    # ------------------------------------------------------------------

    def _cmd_start(self) -> BotResponse:
        return BotResponse(text=get_text("WELCOME"))

    def _cmd_rates(self) -> BotResponse:
        buy_rate = int(get_setting("buy_rate") or 1480)
        sell_rate = int(get_setting("sell_rate") or 1520)
        header = get_text("RATES_HEADER")
        text = (
            f"{header}\n\n"
            f"📈 *I Buy USDT* (you sell to me): ₦{buy_rate}/USDT\n"
            f"📉 *I Sell USDT* (you buy from me): ₦{sell_rate}/USDT\n\n"
            "Type 'buy' or 'sell' to start a trade."
        )
        return BotResponse(text=text)

    def _cmd_history(self, user_id: int) -> BotResponse:
        txs = get_user_transactions(user_id, limit=10)
        if not txs:
            return BotResponse(text=get_text("HISTORY_EMPTY"))
        msg = "📊 *Recent P2P Activity*\n\n"
        for tx in txs:
            icon = "✅" if tx["status"] == "completed" else "⏳" if tx["status"] == "pending" else "❌"
            date_str = tx["created_at"][:10]
            msg += f"{icon} {tx['type'].upper()} | {tx['amount']:.2f} {tx['amount_currency']} | {date_str}\n"
        return BotResponse(text=msg)

    def _cmd_support(self) -> BotResponse:
        admin_id = ADMIN_IDS[0]
        return BotResponse(text=get_text("SUPPORT", admin_id=admin_id))

    # ------------------------------------------------------------------
    # BUY flow
    # ------------------------------------------------------------------

    def _cmd_buy_start(self, user_id: int) -> BotResponse:
        self._new_session(user_id, flow="buy")
        session = self._session(user_id)
        session.state = BUY_AMOUNT
        return BotResponse(text=get_text("BUY_START"), expects_input=True)

    def _buy_amount(self, msg: IncomingMessage, session: ConversationState) -> BotResponse:
        try:
            amount = float(msg.text.strip())
        except ValueError:
            return BotResponse(text=get_text("INVALID_AMOUNT"))
        if amount < MIN_TRADE_USDT:
            return BotResponse(
                text=f"❌ Minimum trade is {MIN_TRADE_USDT} USDT. Please enter a higher amount."
            )
        if amount > MAX_TRADE_USDT:
            return BotResponse(
                text=f"❌ Maximum trade is {MAX_TRADE_USDT:,.0f} USDT. For larger amounts, contact support."
            )
        session.data["buy_amount"] = amount
        session.state = BUY_WALLET
        self._persist_session(msg.user_id)
        return BotResponse(
            text=get_text("BUY_AMOUNT_SUCCESS", amount=amount),
            expects_input=True,
        )

    def _buy_wallet(self, msg: IncomingMessage, session: ConversationState) -> BotResponse:
        wallet = msg.text.strip()
        if not TRC20_REGEX.match(wallet):
            return BotResponse(text=get_text("BUY_WALLET_INVALID"))
        session.data["buy_wallet"] = wallet
        session.state = BUY_CONFIRM_WALLET
        self._persist_session(msg.user_id)
        return BotResponse(text=get_text("BUY_WALLET_DOUBLE_CHECK"), expects_input=True)

    def _buy_confirm_wallet(
        self, msg: IncomingMessage, session: ConversationState
    ) -> BotResponse:
        wallet_confirm = msg.text.strip()
        if wallet_confirm != session.data["buy_wallet"]:
            session.state = BUY_WALLET
            self._persist_session(msg.user_id)
            return BotResponse(text=get_text("WALLET_MISMATCH"))
        sell_rate = int(get_setting("sell_rate") or 1520)
        naira_total = session.data["buy_amount"] * sell_rate
        session.state = BUY_PAYMENT_PROOF
        self._persist_session(msg.user_id)
        return BotResponse(
            text=get_text(
                "BUY_PAYMENT_DETAILS",
                amount=session.data["buy_amount"],
                naira=naira_total,
                bank=YOUR_BANK_NAME,
                acc=YOUR_BANK_ACCOUNT,
                name=YOUR_BANK_ACCOUNT_NAME,
            ),
            expects_input=True,
        )

    def _buy_payment_proof(
        self, msg: IncomingMessage, session: ConversationState
    ) -> BotResponse:
        sell_rate = int(get_setting("sell_rate") or 1520)
        amount = session.data["buy_amount"]
        wallet = session.data["buy_wallet"]
        naira = amount * sell_rate
        user_id = msg.user_id

        tx_id = add_transaction(
            user_id=user_id, tx_type="buy", amount_currency="USDT",
            amount=amount, rate=sell_rate, status="pending",
            details=f"Recipient Wallet: {wallet}",
        )

        admin_msg = (
            f"🚨 *TRADE: BUY ORDER #{tx_id}*\n\n"
            f"Client ID: `{user_id}`\n"
            f"Requested: {amount} USDT\n"
            f"Expected: ₦{naira:,.2f}\n"
            f"🎯 *Target Wallet:* `{wallet}`"
        )
        buttons = [[
            Button(label="✅ Approve (Credit User)", callback_data=f"admin_approve_{tx_id}"),
            Button(label="❌ Reject (Wait)", callback_data=f"admin_reject_{tx_id}"),
        ]]

        self._notify_admin(
            chat_id=str(ADMIN_IDS[0]),
            text=admin_msg,
            buttons=buttons,
            photo_url=(
                msg.attachments[0].file_url or msg.attachments[0].file_path
                if msg.attachments and msg.attachments[0].type == AttachmentType.PHOTO
                else ""
            ),
        )

        self._end_session(user_id)
        return BotResponse(text=get_text("BUY_ORDER_COMPLETE", tx_id=tx_id))

    # ------------------------------------------------------------------
    # SELL flow
    # ------------------------------------------------------------------

    def _cmd_sell_start(self, user_id: int) -> BotResponse:
        self._new_session(user_id, flow="sell")
        session = self._session(user_id)
        session.state = SELL_AMOUNT
        return BotResponse(text=get_text("SELL_START"), expects_input=True)

    def _sell_amount(self, msg: IncomingMessage, session: ConversationState) -> BotResponse:
        try:
            amount = float(msg.text.strip())
        except ValueError:
            return BotResponse(text=get_text("INVALID_AMOUNT"))
        if amount < MIN_TRADE_USDT:
            return BotResponse(
                text=f"❌ Minimum trade is {MIN_TRADE_USDT} USDT. Please enter a higher amount."
            )
        if amount > MAX_TRADE_USDT:
            return BotResponse(
                text=f"❌ Maximum trade is {MAX_TRADE_USDT:,.0f} USDT. For larger amounts, contact support."
            )
        session.data["sell_amount"] = amount
        session.state = SELL_BANK_DETAILS
        self._persist_session(msg.user_id)
        return BotResponse(
            text=get_text("SELL_AMOUNT_SUCCESS", amount=amount),
            expects_input=True,
        )

    def _sell_bank_details(
        self, msg: IncomingMessage, session: ConversationState
    ) -> BotResponse:
        details = msg.text.strip()
        acc_num_match = re.search(r"\d{10}", details)
        if not acc_num_match:
            return BotResponse(text=get_text("SELL_BANK_INVALID"))
        session.data["sell_bank"] = details
        session.data["sell_acc_num"] = acc_num_match.group(0)
        session.state = SELL_CONFIRM_ACC
        self._persist_session(msg.user_id)
        return BotResponse(text=get_text("SELL_BANK_DOUBLE_CHECK"), expects_input=True)

    def _sell_confirm_acc(
        self, msg: IncomingMessage, session: ConversationState
    ) -> BotResponse:
        acc_confirm = msg.text.strip()
        if acc_confirm != session.data["sell_acc_num"]:
            session.state = SELL_BANK_DETAILS
            self._persist_session(msg.user_id)
            return BotResponse(text=get_text("ACC_MISMATCH"))
        buy_rate = int(get_setting("buy_rate") or 1480)
        naira_total = session.data["sell_amount"] * buy_rate
        session.state = SELL_TX_HASH
        self._persist_session(msg.user_id)
        return BotResponse(
            text=get_text(
                "SELL_INSTRUCTIONS",
                amount=session.data["sell_amount"],
                wallet=YOUR_USDT_WALLET,
            ),
            expects_input=True,
        )

    def _sell_tx_hash(
        self, msg: IncomingMessage, session: ConversationState
    ) -> BotResponse:
        tx_hash = msg.text.strip()

        # Validate TXID format: 64 hex chars
        if not TX_HASH_REGEX.match(tx_hash):
            return BotResponse(
                text=(
                    "❌ Invalid transaction hash format. "
                    "A TRON TXID is 64 hex characters (e.g., `a1b2c3d4...`). "
                    "Please check and re-enter."
                )
            )

        buy_rate = int(get_setting("buy_rate") or 1480)
        amount = session.data["sell_amount"]
        bank_details = session.data["sell_bank"]
        naira = amount * buy_rate
        user_id = msg.user_id

        tx_id = add_transaction(
            user_id=user_id, tx_type="sell", amount_currency="USDT",
            amount=amount, rate=buy_rate, status="pending",
            tx_hash=tx_hash, details=f"Bank Settlement: {bank_details}",
        )

        admin_msg = (
            f"🚨 *TRADE: SELL ORDER #{tx_id}*\n\n"
            f"Client ID: `{user_id}`\n"
            f"Selling: {amount} USDT\n"
            f"Payable: ₦{naira:,.2f}\n"
            f"🏦 *Target Bank:* {bank_details}\n"
            f"🔗 *Hash:* `{tx_hash}`"
        )
        buttons = [[
            Button(label="✅ Approve (Paid)", callback_data=f"admin_approve_{tx_id}"),
            Button(label="❌ Reject (Wait)", callback_data=f"admin_reject_{tx_id}"),
        ]]

        self._notify_admin(
            chat_id=str(ADMIN_IDS[0]),
            text=admin_msg,
            buttons=buttons,
        )

        self._end_session(user_id)
        return BotResponse(text=get_text("SELL_ORDER_COMPLETE", tx_id=tx_id))

    # ------------------------------------------------------------------
    # Active conversation router
    # ------------------------------------------------------------------

    def _handle_conversation(
        self, msg: IncomingMessage, session: ConversationState
    ) -> BotResponse:
        state = session.state
        if state == BUY_AMOUNT:
            return self._buy_amount(msg, session)
        elif state == BUY_WALLET:
            return self._buy_wallet(msg, session)
        elif state == BUY_CONFIRM_WALLET:
            return self._buy_confirm_wallet(msg, session)
        elif state == BUY_PAYMENT_PROOF:
            return self._buy_payment_proof(msg, session)
        elif state == SELL_AMOUNT:
            return self._sell_amount(msg, session)
        elif state == SELL_BANK_DETAILS:
            return self._sell_bank_details(msg, session)
        elif state == SELL_CONFIRM_ACC:
            return self._sell_confirm_acc(msg, session)
        elif state == SELL_TX_HASH:
            return self._sell_tx_hash(msg, session)
        else:
            logger.warning(f"Unknown state {state} for user {msg.user_id}")
            self._end_session(msg.user_id)
            return BotResponse(text=get_text("CANCEL_TRADE"))

    # ------------------------------------------------------------------
    # Admin approval / rejection
    # ------------------------------------------------------------------

    def handle_admin_action(
        self, admin_user_id: int, action: str, tx_id: int,
        target_chat_id: str | int,
    ) -> BotResponse:
        if admin_user_id not in ADMIN_IDS:
            return BotResponse(text="⛔ Unauthorized access attempt.")
        tx = get_transaction(tx_id)
        if not tx:
            return BotResponse(text="❌ Transaction record not found.")
        if tx["status"] == "completed":
            return BotResponse(text="ℹ️ This order has already been finalized.")

        tx_user_id = tx["user_id"]

        if action == "approve":
            update_transaction_status(tx_id, "completed")
            try:
                self._notify_user(
                    chat_id=str(tx_user_id),
                    text=get_text("ADMIN_APPROVE_USER", tx_id=tx_id),
                )
            except Exception as e:
                logger.error(f"Failed to notify user {tx_user_id}: {e}")
            return BotResponse(text=f"✅ Order #{tx_id} finalized and marked as COMPLETED.")

        elif action == "reject":
            if tx["status"] == "failed":
                return BotResponse(text="ℹ️ Order is already in a rejected state.")
            update_transaction_status(tx_id, "failed")
            buttons = [[
                Button(
                    label="✅ Re-approve (Funds Received)",
                    callback_data=f"admin_approve_{tx_id}",
                )
            ]]
            try:
                self._notify_user(
                    chat_id=str(tx_user_id),
                    text=get_text("ADMIN_REJECT_USER", tx_id=tx_id),
                )
            except Exception as e:
                logger.error(f"Failed to notify user {tx_user_id}: {e}")
            return BotResponse(
                text=(
                    f"❌ Order #{tx_id} REJECTED (Pending funds).\n\n"
                    "You may still approve this trade if funds reflect later."
                ),
                buttons=buttons,
            )
        elif action == "resolve":
            # Manual resolution for edge cases
            update_transaction_status(tx_id, "completed")
            try:
                self._notify_user(
                    chat_id=str(tx_user_id),
                    text=get_text("ADMIN_APPROVE_USER", tx_id=tx_id),
                )
            except Exception as e:
                logger.error(f"Failed to notify user {tx_user_id}: {e}")
            return BotResponse(text=f"✅ Order #{tx_id} manually resolved and completed.")

        return BotResponse(text="Unknown action.")

    # ------------------------------------------------------------------
    # Admin commands
    # ------------------------------------------------------------------

    def handle_admin_command(
        self, admin_user_id: int, command: str, args: list[str]
    ) -> BotResponse:
        if admin_user_id not in ADMIN_IDS:
            return BotResponse(text="Permission Denied.")

        handler = {
            "setrate": self._cmd_setrate,
            "broadcast": lambda a: BotResponse(text="BROADCAST_DEFERRED"),
            "stats": self._cmd_stats,
            "pending": self._cmd_pending,
            "user": self._cmd_user,
            "ban": self._cmd_ban,
            "unban": self._cmd_unban,
            "resolve": self._cmd_resolve,
        }.get(command)

        if handler:
            return handler(args)
        return BotResponse(text=f"Unknown admin command: {command}")

    def _cmd_setrate(self, args: list[str]) -> BotResponse:
        if len(args) != 2:
            return BotResponse(text="Usage: `/setrate <buy_price> <sell_price>`")
        try:
            buy_rate, sell_rate = int(args[0]), int(args[1])
            if sell_rate <= buy_rate:
                return BotResponse(text="Market Rule Error: Sell rate must exceed buy rate.")
            set_setting("buy_rate", str(buy_rate))
            set_setting("sell_rate", str(sell_rate))
            return BotResponse(
                text=f"✅ Rates Synchronized:\n📈 Buy: ₦{buy_rate}\n📉 Sell: ₦{sell_rate}"
            )
        except ValueError:
            return BotResponse(text="Input Error: Rates must be valid integers.")

    def _cmd_stats(self, args: list[str]) -> BotResponse:
        stats = get_transaction_stats()
        users = get_user_count()
        text = (
            f"📊 *Bot Statistics*\n\n"
            f"👥 Total Users: {users}\n"
            f"📋 Total Transactions: {stats['total_count']}\n"
            f"⏳ Pending: {stats['pending_count']}\n"
            f"✅ Completed: {stats['completed_count']}\n"
            f"❌ Failed: {stats['failed_count']}\n"
            f"💰 Total USDT Volume: {stats['total_usdt_volume']:,.2f}\n"
            f"💵 Total NGN Volume: ₦{stats['total_ngn_volume']:,.2f}"
        )
        return BotResponse(text=text)

    def _cmd_pending(self, args: list[str]) -> BotResponse:
        pending = get_pending_transactions(limit=20)
        if not pending:
            return BotResponse(text="✅ No pending transactions.")

        lines = ["⏳ *Pending Transactions*\n"]
        for tx in pending:
            icon = "🟢" if tx["status"] == "pending" else "🔴"
            date_str = tx.get("created_at", "")[:10]
            lines.append(
                f"{icon} `#{tx['id']}` | {tx['type'].upper()} | "
                f"{tx['amount']} {tx['amount_currency']} | "
                f"User `{tx['user_id']}` | {date_str}"
            )

        # Build inline buttons for first 5 pending
        buttons = []
        for tx in pending[:5]:
            buttons.append([
                Button(label=f"✅ Approve #{tx['id']}", callback_data=f"admin_approve_{tx['id']}"),
                Button(label=f"❌ Reject #{tx['id']}", callback_data=f"admin_reject_{tx['id']}"),
            ])

        return BotResponse(text="\n".join(lines), buttons=buttons)

    def _cmd_user(self, args: list[str]) -> BotResponse:
        if not args:
            return BotResponse(text="Usage: `/user <user_id>`")
        try:
            target_id = int(args[0])
        except ValueError:
            return BotResponse(text="❌ Invalid user ID. Must be a number.")

        user = get_user(target_id)
        if not user:
            return BotResponse(text=f"❌ User `{target_id}` not found.")

        txs = get_user_transactions(target_id, limit=5)
        banned = "🚫 YES" if is_banned(target_id) else "✅ No"

        lines = [
            f"👤 *User Profile: {target_id}*\n",
            f"Banned: {banned}",
            f"Phone: {user.get('phone', 'N/A')}",
            f"Bank: {user.get('bank_name', 'N/A')} — {user.get('bank_account_number', 'N/A')}",
            f"Wallet: `{user.get('crypto_address', 'N/A')}`",
            f"NGN Balance: ₦{user.get('naira_balance', 0):,.2f}",
            f"USDT Balance: {user.get('usdt_balance', 0):,.2f}",
            f"\n📊 *Recent Transactions:*",
        ]

        if txs:
            for tx in txs:
                icon = "✅" if tx["status"] == "completed" else "⏳" if tx["status"] == "pending" else "❌"
                date_str = tx.get("created_at", "")[:10]
                lines.append(
                    f"{icon} {tx['type'].upper()} | {tx['amount']} {tx['amount_currency']} | {date_str}"
                )
        else:
            lines.append("No transactions yet.")

        return BotResponse(text="\n".join(lines))

    def _cmd_ban(self, args: list[str]) -> BotResponse:
        if not args:
            return BotResponse(text="Usage: `/ban <user_id> [reason]`")
        try:
            target_id = int(args[0])
        except ValueError:
            return BotResponse(text="❌ Invalid user ID.")
        reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"
        if ban_user(target_id, reason):
            return BotResponse(text=f"🚫 User `{target_id}` has been banned.\nReason: {reason}")
        return BotResponse(text="❌ Failed to ban user.")

    def _cmd_unban(self, args: list[str]) -> BotResponse:
        if not args:
            return BotResponse(text="Usage: `/unban <user_id>`")
        try:
            target_id = int(args[0])
        except ValueError:
            return BotResponse(text="❌ Invalid user ID.")
        if unban_user(target_id):
            return BotResponse(text=f"✅ User `{target_id}` has been unbanned.")
        return BotResponse(text="❌ Failed to unban user.")

    def _cmd_resolve(self, args: list[str]) -> BotResponse:
        if not args:
            return BotResponse(text="Usage: `/resolve <tx_id>`")
        try:
            tx_id = int(args[0])
        except ValueError:
            return BotResponse(text="❌ Invalid transaction ID.")
        return self.handle_admin_action(ADMIN_IDS[0], "resolve", tx_id, ADMIN_IDS[0])

    # ------------------------------------------------------------------
    # Reminder text
    # ------------------------------------------------------------------

    @staticmethod
    def get_reminder_text() -> str:
        return get_text("REMINDER")
