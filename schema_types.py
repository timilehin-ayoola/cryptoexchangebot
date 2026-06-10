"""
Platform-agnostic data types for the P2P Crypto Exchange Bot.

These types define the boundary between platform adapters (Telegram, WhatsApp, etc.)
and the core bot logic. No platform-specific imports allowed here.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

class AttachmentType(enum.Enum):
    """Classification of user-submitted media."""
    PHOTO = "photo"
    DOCUMENT = "document"
    NONE = "none"


@dataclass
class Attachment:
    """A single piece of media sent by the user."""
    type: AttachmentType
    file_id: str = ""           # platform-specific identifier
    file_url: str = ""          # direct URL if available
    file_path: str = ""         # local path if downloaded
    mime_type: str = ""         # e.g. "image/jpeg", "application/pdf"


# ---------------------------------------------------------------------------
# Incoming messages (adapter → engine)
# ---------------------------------------------------------------------------

@dataclass
class IncomingMessage:
    """Normalized message from any platform, ready for the engine to process."""
    user_id: int
    chat_id: str | int          # platform-specificchat identifier
    text: str = ""
    attachments: list[Attachment] = field(default_factory=list)
    platform: str = ""          # "telegram", "whatsapp", etc.
    timestamp: datetime = field(default_factory=datetime.now)

    # Raw platform payload — adapter-specific, engine should never touch this
    raw: object = None


# ---------------------------------------------------------------------------
# Outgoing messages (engine → adapter)
# ---------------------------------------------------------------------------

@dataclass
class Button:
    """Abstract inline button. Adapter maps this to platform-specific markup."""
    label: str
    callback_data: str = ""     # engine-level action identifier
    url: str = ""               # optional link button


@dataclass
class BotResponse:
    """Platform-agnostic bot response. Adapter translates to send_message/photo/etc."""
    text: str = ""
    buttons: list[list[Button]] = field(default_factory=list)  # rows of buttons
    parse_mode: str = "Markdown"
    photo_url: str = ""         # send photo instead of text if set
    document_path: str = ""     # send document if set
    # If set, the engine expects user input next and will route to this state
    expects_input: bool = True


# ---------------------------------------------------------------------------
# Conversation session (engine internal state)
# ---------------------------------------------------------------------------

@dataclass
class ConversationState:
    """Tracks where a user is inside a multi-step flow."""
    state: int = 0
    flow: str = ""              # "buy" or "sell"
    data: dict = field(default_factory=dict)  # accumulated step data


# ---------------------------------------------------------------------------
# Transaction record (shared across engine and business logic)
# ---------------------------------------------------------------------------

class TransactionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransactionType(enum.Enum):
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"


@dataclass
class TransactionRecord:
    """Normalized transaction as stored/returned by the database layer."""
    id: int
    user_id: int
    tx_type: TransactionType
    amount_currency: str
    amount: float
    rate: float
    status: TransactionStatus
    tx_hash: Optional[str] = None
    details: Optional[str] = None
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

@dataclass
class UserProfile:
    """Normalized user record."""
    user_id: int
    phone: str = ""
    bank_name: str = ""
    bank_account_name: str = ""
    bank_account_number: str = ""
    crypto_address: str = ""
    naira_balance: float = 0.0
    usdt_balance: float = 0.0
