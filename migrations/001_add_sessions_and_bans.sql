-- Database migration for bot_cryptoexchangebot
-- Run this in your Supabase SQL editor to add new tables

-- ============================================================================
-- SESSION PERSISTENCE
-- Survives bot restores mid-conversation if the bot restarts
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_sessions (
    user_id     BIGINT PRIMARY KEY,
    flow        TEXT NOT NULL,
    state       INT NOT NULL DEFAULT 0,
    data        JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Index for cleanup of stale sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_updated
    ON user_sessions (updated_at);


-- ============================================================================
-- BAN SYSTEM
-- Prevent abusive users from trading
-- ============================================================================

CREATE TABLE IF NOT EXISTS bans (
    user_id     BIGINT PRIMARY KEY,
    reason      TEXT DEFAULT '',
    banned_at   TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- NOTES
-- ============================================================================
-- user_sessions:  Engine automatically saves/loads on each state transition.
--                 Stale sessions (>24h) are cleaned up on startup.
--
-- bans:           Engine checks on every message. Banned users get
--                 a block response and cannot start trades.
--
-- Existing tables (users, transactions, settings) remain unchanged.
