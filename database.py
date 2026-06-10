"""
Database management module for the Nigerian P2P Crypto Exchange Bot.
Interfaces with Neon (PostgreSQL) for persistent data storage.

Sections:
    - User Management
    - Session Persistence
    - Transaction Management
    - Settings Management
    - Admin Queries
"""

import json
import logging
from typing import List, Dict, Optional, Any

import psycopg2
import psycopg2.extras
from config import DATABASE_URL

logger = logging.getLogger(__name__)

if not DATABASE_URL:
    logger.critical("DATABASE_URL must be set in .env")
    raise ValueError("Missing database credentials.")


def _get_conn():
    """Get a new database connection."""
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# ============================================================================
# INITIALISATION
# ============================================================================

def init_db() -> None:
    """Run schema migration and set defaults on startup."""
    logger.info("Initializing database schema...")
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        user_id             BIGINT PRIMARY KEY,
        phone               TEXT NOT NULL DEFAULT '',
        bank_name           TEXT NOT NULL DEFAULT '',
        bank_account_name   TEXT NOT NULL DEFAULT '',
        bank_account_number TEXT NOT NULL DEFAULT '',
        crypto_address      TEXT NOT NULL DEFAULT '',
        naira_balance       NUMERIC(12,2) NOT NULL DEFAULT 0.00,
        usdt_balance        NUMERIC(12,2) NOT NULL DEFAULT 0.00,
        created_at          TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id              SERIAL PRIMARY KEY,
        user_id         BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        type            TEXT NOT NULL,
        amount_currency TEXT NOT NULL,
        amount          NUMERIC(12,2) NOT NULL,
        rate            NUMERIC(12,2) NOT NULL,
        status          TEXT NOT NULL DEFAULT 'pending',
        tx_hash         TEXT,
        details         TEXT,
        created_at      TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions (user_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions (status);

    CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS user_sessions (
        user_id     BIGINT PRIMARY KEY,
        flow        TEXT NOT NULL,
        state       INT NOT NULL DEFAULT 0,
        data        JSONB NOT NULL DEFAULT '{}'::jsonb,
        updated_at  TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_user_sessions_updated
        ON user_sessions (updated_at);

    CREATE TABLE IF NOT EXISTS bans (
        user_id     BIGINT PRIMARY KEY,
        reason      TEXT DEFAULT '',
        banned_at   TIMESTAMPTZ DEFAULT NOW()
    );

    INSERT INTO settings (key, value) VALUES
        ('buy_rate', '1480'),
        ('sell_rate', '1520'),
        ('last_reminder_date', '')
    ON CONFLICT (key) DO NOTHING;
    """
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        conn.close()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")


def set_setting_if_not_exists(key: str, value: str) -> None:
    existing = get_setting(key)
    if existing is None:
        set_setting(key, value)


# ============================================================================
# USER MANAGEMENT
# ============================================================================

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
        conn.close()
        if row:
            return dict(row)
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
    return None


def register_user(
    user_id: int, phone: str, bank_name: str, bank_account_name: str,
    bank_account_number: str, crypto_address: str,
) -> None:
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO users (user_id, phone, bank_name, bank_account_name,
                   bank_account_number, crypto_address)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT (user_id) DO UPDATE SET
                   phone = EXCLUDED.phone,
                   bank_name = EXCLUDED.bank_name,
                   bank_account_name = EXCLUDED.bank_account_name,
                   bank_account_number = EXCLUDED.bank_account_number,
                   crypto_address = EXCLUDED.crypto_address""",
                (user_id, phone, bank_name, bank_account_name,
                 bank_account_number, crypto_address),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error upserting user {user_id}: {e}")


def auto_create_user(user_id: int) -> Dict[str, Any]:
    user = get_user(user_id)
    if not user:
        logger.info(f"Creating new profile for user {user_id}")
        register_user(user_id, "", "", "", "", "")
        user = get_user(user_id)
    return user or {}


def update_balance(user_id: int, naira_delta: float = 0.0, usdt_delta: float = 0.0) -> None:
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE users SET
                   naira_balance = COALESCE(naira_balance, 0) + %s,
                   usdt_balance = COALESCE(usdt_balance, 0) + %s
                   WHERE user_id = %s""",
                (naira_delta, usdt_delta, user_id),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating balance for {user_id}: {e}")


# ============================================================================
# SESSION PERSISTENCE  (survives bot restarts)
# ============================================================================

def save_session(user_id: int, flow: str, state: int, data: dict) -> None:
    """Upsert an active conversation session."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO user_sessions (user_id, flow, state, data, updated_at)
                   VALUES (%s, %s, %s, %s::jsonb, NOW())
                   ON CONFLICT (user_id) DO UPDATE SET
                   flow = EXCLUDED.flow,
                   state = EXCLUDED.state,
                   data = EXCLUDED.data,
                   updated_at = NOW()""",
                (user_id, flow, state, json.dumps(data)),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving session for {user_id}: {e}")


def load_session(user_id: int) -> Optional[Dict[str, Any]]:
    """Load an active session for a user, or None."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM user_sessions WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
        conn.close()
        if row:
            row = dict(row)
            if isinstance(row.get("data"), str):
                row["data"] = json.loads(row["data"])
            return row
    except Exception as e:
        logger.error(f"Error loading session for {user_id}: {e}")
    return None


def delete_session(user_id: int) -> None:
    """Remove a completed/expired session."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error deleting session for {user_id}: {e}")


def load_all_sessions() -> List[Dict[str, Any]]:
    """Load all active sessions (called on startup to restore state)."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM user_sessions")
            rows = cur.fetchall()
        conn.close()
        sessions = []
        for row in rows:
            row = dict(row)
            try:
                if isinstance(row.get("data"), str):
                    row["data"] = json.loads(row["data"])
                sessions.append(row)
            except (json.JSONDecodeError, TypeError):
                continue
        return sessions
    except Exception as e:
        logger.error(f"Error loading all sessions: {e}")
    return []


def cleanup_stale_sessions(max_age_hours: int = 24) -> int:
    """Remove sessions older than max_age_hours. Returns count deleted."""
    try:
        from datetime import datetime, timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM user_sessions WHERE updated_at < %s",
                (cutoff,),
            )
            count = cur.rowcount
        conn.commit()
        conn.close()
        if count:
            logger.info(f"Cleaned up {count} stale sessions")
        return count
    except Exception as e:
        logger.error(f"Error cleaning stale sessions: {e}")
    return 0


# ============================================================================
# TRANSACTION MANAGEMENT
# ============================================================================

def add_transaction(
    user_id: int, tx_type: str, amount_currency: str, amount: float,
    rate: float, status: str, tx_hash: Optional[str] = None,
    details: Optional[str] = None,
) -> Optional[int]:
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO transactions
                   (user_id, type, amount_currency, amount, rate, status, tx_hash, details)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (user_id, tx_type, amount_currency, amount, rate,
                 status, tx_hash, details),
            )
            tx_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return tx_id
    except Exception as e:
        logger.error(f"Error adding transaction for {user_id}: {e}")
    return None


def update_transaction_status(tx_id: int, status: str) -> None:
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE transactions SET status = %s WHERE id = %s",
                (status, tx_id),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating transaction {tx_id}: {e}")


def get_transaction(tx_id: int) -> Optional[Dict[str, Any]]:
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM transactions WHERE id = %s", (tx_id,))
            row = cur.fetchone()
        conn.close()
        if row:
            return dict(row)
    except Exception as e:
        logger.error(f"Error fetching transaction {tx_id}: {e}")
    return None


def get_user_transactions(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                (user_id, limit),
            )
            rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error fetching history for {user_id}: {e}")
    return []


# ============================================================================
# SETTINGS MANAGEMENT
# ============================================================================

def get_setting(key: str) -> Optional[str]:
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM settings WHERE key = %s", (key,))
            row = cur.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception as e:
        logger.error(f"Error fetching setting {key}: {e}")
    return None


def set_setting(key: str, value: str) -> None:
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO settings (key, value) VALUES (%s, %s)
                   ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
                (key, str(value)),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error setting {key}: {e}")


# ============================================================================
# USER QUERIES
# ============================================================================

def get_all_users() -> List[int]:
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users")
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching all users: {e}")
    return []


# ============================================================================
# ADMIN BAN SYSTEM
# ============================================================================

def ban_user(user_id: int, reason: str = "") -> bool:
    """Ban a user from trading. Returns True if successful."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO bans (user_id, reason, banned_at)
                   VALUES (%s, %s, NOW())
                   ON CONFLICT (user_id) DO UPDATE SET
                   reason = EXCLUDED.reason, banned_at = NOW()""",
                (user_id, reason),
            )
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} banned. Reason: {reason}")
        return True
    except Exception as e:
        logger.error(f"Error banning user {user_id}: {e}")
    return False


def unban_user(user_id: int) -> bool:
    """Remove a user's ban. Returns True if successful."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bans WHERE user_id = %s", (user_id,))
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} unbanned.")
        return True
    except Exception as e:
        logger.error(f"Error unbanning user {user_id}: {e}")
    return False


def is_banned(user_id: int) -> bool:
    """Check if a user is currently banned."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM bans WHERE user_id = %s", (user_id,))
            result = cur.fetchone() is not None
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Error checking ban for {user_id}: {e}")
    return False


def get_banned_users() -> List[Dict[str, Any]]:
    """Get all banned users."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM bans")
            rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error fetching banned users: {e}")
    return []


# ============================================================================
# ADMIN STATS & QUERIES
# ============================================================================

def get_pending_transactions(limit: int = 20) -> List[Dict[str, Any]]:
    """Get all pending transactions for admin review."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM transactions WHERE status = 'pending' ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error fetching pending transactions: {e}")
    return []


def get_user_count() -> int:
    """Total number of registered users."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
        conn.close()
        return count or 0
    except Exception as e:
        logger.error(f"Error counting users: {e}")
    return 0


def get_transaction_stats() -> Dict[str, Any]:
    """Aggregate stats: total volume, counts by status."""
    stats = {
        "total_count": 0,
        "pending_count": 0,
        "completed_count": 0,
        "failed_count": 0,
        "total_usdt_volume": 0.0,
        "total_ngn_volume": 0.0,
    }
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM transactions")
            rows = cur.fetchall()
        conn.close()
        for tx in rows:
            stats["total_count"] += 1
            status = tx.get("status")
            if status == "pending":
                stats["pending_count"] += 1
            elif status == "completed":
                stats["completed_count"] += 1
            elif status == "failed":
                stats["failed_count"] += 1
            if tx.get("amount_currency") == "USDT":
                stats["total_usdt_volume"] += tx.get("amount", 0) or 0
            elif tx.get("amount_currency") == "NGN":
                stats["total_ngn_volume"] += tx.get("amount", 0) or 0
    except Exception as e:
        logger.error(f"Error computing transaction stats: {e}")
    return stats