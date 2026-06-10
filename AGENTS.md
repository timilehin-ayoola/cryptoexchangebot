# AGENTS.md — Nigerian P2P Crypto Exchange Bot

_Project-level agent orchestration and context file. Loaded by every agent working on this project._

---

## Project Identity

**Name:** Nigerian P2P Crypto Exchange Bot
**Type:** Telegram bot — USDT/Naira P2P trading
**Language:** Python 3.11+
**Platform:** python-telegram-bot >=21.1 (<22.0)
**Database:** Supabase (PostgreSQL)
**Blockchain:** TRON (TRC20 USDT via TronGrid)
**Deployment:** Render

---

## Architecture

```
bot.py              → Entry point, Telegram app bootstrap
engine.py           → Platform-agnostic conversation state machine (ALL business logic)
schema_types.py     → Data types (IncomingMessage, BotResponse, ConversationState)
adapters/           → Platform-specific I/O (telegram_adapter.py)
middleware/         → Rate limiter, anti-spam (rate_limiter.py)
database.py         → Supabase CRUD layer
config.py           → Environment variables, trading parameters
responses.py        → 200+ Nigerian Pidgin English response variations
utils/              → tron_utils.py (blockchain), bank_utils.py (payments)
migrations/         → Supabase SQL migrations
```

**Critical design rule:** `engine.py` has ZERO Telegram imports. All platform I/O goes through
the adapter pattern. Adding WhatsApp/web later should NOT require touching engine.py.

---

## Agent Pipeline

This project follows the **Software Factory** pattern:

```
Story → Spec → Backend Build → Response/Localization Build → Test Verify → Validate

Approval Gates:
  Gate 1: Story approved (after story-writer)
  Gate 2: Spec approved (after spec-writer)
  Gate 3: Final validation (after implementation-validator)
```

**Orchestrator:** Apex runs the chain. Agents do focused work in their own context.

---

## Code Standards

1. Engine must remain platform-agnostic — no Telegram imports in engine.py
2. All user-facing text goes through `responses.get_text()` (Nigerian Pidgin English)
3. All DB operations go through `database.py`
4. TRC20 regex: `^T[1-9A-HJ-NP-Za-km-z]{33}$`
5. TX hash regex: `^[a-fA-F0-9]{64}$`
6. Trade bounds: MIN=1.0 USDT, MAX=10,000.0 USDT
7. Max 3 pending transactions per user
8. Rate limit: 5 req / 30s window, 60s block
9. Session data persists to DB on every state transition
10. Type hints required on all function signatures
11. New files < 200 lines. Split if larger.
12. engine.py must stay under 1000 lines — split into modules if needed

---

## What NOT to Change Without Discussion

- State machine order (BUY_AMOUNT..SELL_TX_HASH)
- Platform-agnostic adapter pattern
- Nigerian Pidgin English tone in responses
- Supabase table schemas (coordinate with migrations/)
- Rate limiter defaults (5/30s/60s)

---

## Directory Conventions

| Path | Purpose |
|------|---------|
| `.agents/` | Agent definitions and project orchestration |
| `.agents/skills/` | Reusable workflow skills |
| `adapters/` | Platform-specific I/O (create new adapter per platform) |
| `middleware/` | Cross-cutting concerns (rate limit, auth, logging) |
| `utils/` | Pure utility functions (blockchain, bank) |
| `migrations/` | SQL files for Supabase schema changes |
| `tests/` | pytest test suite |

---

## Feature Request Protocol (DMP)

1. **Research** — codebase-researcher maps the relevant code
2. **Triage** — story-writer turns the idea into a user story
3. **Brief** — spec-writer creates a technical spec
4. **Approval** — human reviews and approves spec
5. **Execution** — backend-builder + test-verifier + implementation-validator run the chain

Every feature follows this pipeline. No exceptions.
