"""
Configuration module for the Nigerian P2P Crypto Exchange Bot.

This module handles environment variable loading and provides a centralized settings interface
for Telegram, Supabase (database), blockchain (TRON), and merchant bank details.

Environment variables should be defined in a .env file or through the hosting provider's
configuration panel. See .env.example for required variables.
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file (optional if using hosting provider config)
load_dotenv()


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Safely retrieve an environment variable with optional default value.

    Args:
        key: The environment variable key to retrieve.
        default: Default value if the key is not found. Defaults to None.
        required: If True, prints a warning if the key is missing. Defaults to False.

    Returns:
        str: The environment variable value or the default value.

    Note:
        Logging may not be initialized at config load time, so print() is used for warnings.
    """
    value = os.getenv(key, default)
    if required and not value:
        print(f"⚠️  CONFIG WARNING: Missing environment variable: {key}")
    return value or ""


# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================

BOT_TOKEN: str = get_env("BOT_TOKEN", required=True)
"""Telegram bot API token from BotFather. Required."""

ADMIN_ID_RAW: str = get_env("ADMIN_ID", required=True)
"""Raw admin user ID(s) from environment variable."""

ADMIN_IDS: List[int] = (
    [int(ADMIN_ID_RAW)] if ADMIN_ID_RAW and ADMIN_ID_RAW.isdigit() else []
)
"""List of admin user IDs with elevated permissions."""


# ============================================================================
# DATABASE CONFIGURATION (Neon PostgreSQL)
# ============================================================================

DATABASE_URL: str = get_env("DATABASE_URL", required=True)
"""Neon PostgreSQL connection string (postgresql://user:pass@ep-xxx.neon.tech/neondb)."""


# ============================================================================
# BLOCKCHAIN CONFIGURATION (TRON Network)
# ============================================================================

TRONGRID_API_KEY: str = get_env("TRONGRID_API_KEY", "")
"""TronGrid API key for blockchain queries. Optional but recommended."""

YOUR_USDT_WALLET: str = get_env("YOUR_USDT_WALLET", "TYourWalletAddressHere")
"""Merchant's TRC20 USDT wallet address for receiving customer payments."""


# ============================================================================
# MERCHANT BANK DETAILS (NGN Settlement)
# ============================================================================

YOUR_BANK_NAME: str = get_env("YOUR_BANK_NAME", "Moniepoint Microfinance Bank")
"""Name of the bank for NGN transfers to users."""

YOUR_BANK_ACCOUNT: str = get_env("YOUR_BANK_ACCOUNT", "0000000000")
"""10-digit bank account number for merchant."""

YOUR_BANK_ACCOUNT_NAME: str = get_env("YOUR_BANK_ACCOUNT_NAME", "Business Account")
"""Account holder name displayed to customers."""


# ============================================================================
# TRADING PARAMETERS (Default Exchange Rates)
# ============================================================================

DEFAULT_BUY_RATE: int = 1480
"""Default rate (NGN per USDT) when users buy USDT from the bot."""

DEFAULT_SELL_RATE: int = 1520
"""Default rate (NGN per USDT) when users sell USDT to the bot."""


# ============================================================================
# OPTIONAL INTEGRATIONS
# ============================================================================

PAYSTACK_SECRET_KEY: str = get_env("PAYSTACK_SECRET_KEY", "")
"""Paystack API secret key for payment verification. Optional."""

