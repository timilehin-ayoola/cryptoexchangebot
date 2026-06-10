-- ============================================================================
-- Full Database Schema for Nigerian P2P Crypto Exchange Bot
-- Compatible with Neon (PostgreSQL 15+)
-- Run this once in the Neon SQL editor after creating your project
-- ============================================================================

-- 1. USERS
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

-- 2. TRANSACTIONS
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

-- 3. SETTINGS
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 4. USER SESSIONS (survives restarts)
CREATE TABLE IF NOT EXISTS user_sessions (
    user_id     BIGINT PRIMARY KEY,
    flow        TEXT NOT NULL,
    state       INT NOT NULL DEFAULT 0,
    data        JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_updated
    ON user_sessions (updated_at);

-- 5. BANS
CREATE TABLE IF NOT EXISTS bans (
    user_id     BIGINT PRIMARY KEY,
    reason      TEXT DEFAULT '',
    banned_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Default settings
-- ============================================================================
INSERT INTO settings (key, value) VALUES
    ('buy_rate', '1480'),
    ('sell_rate', '1520'),
    ('last_reminder_date', '')
ON CONFLICT (key) DO NOTHING;