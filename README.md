# Nigerian P2P Crypto Exchange Bot

[![Uptime](https://img.shields.io/website?url=https%3A%2F%2Fapi.telegram.org&label=Bot%20API)](https://core.telegram.org/bots/api)
[![Platform](https://img.shields.io/badge/Platform-Telegram-blue)](https://telegram.org)
[![Language](https://img.shields.io/badge/Language-Python%203.10%2B-green)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-Neon%20%28PostgreSQL%29-00e599)](https://neon.tech)
[![Hosting](https://img.shields.io/badge/Hosting-Render-black)](https://render.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-grade peer-to-peer cryptocurrency exchange bot for the Nigerian market. Built with Python and Telegram, this bot facilitates direct USDT (TRC20) to Nigerian Naira (NGN) trades with localized communication, robust security protocols, and administrative controls.

**Features**: 🇳🇬 Localized in Nigerian Pidgin | 🛡️ Double-verification security | 📊 Real-time exchange rates | 💾 Permanent audit trail | ⚡ Zero-balance architecture

---

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation & Deployment](#installation--deployment)
- [Configuration](#configuration)
- [Usage](#usage)
- [Administration](#administration)
- [Project Structure](#project-structure)
- [Development](#development)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- A Telegram bot (create via [@BotFather](https://t.me/BotFather))
- Neon account (free tier available)
- TRON wallet address for receiving USDT

### 1-Minute Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/crypto_exchange_bot.git
cd crypto_exchange_bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run the bot
python bot.py
```

---

## Features

### 🇳🇬 Localized Experience

- **200+ Response Variations**: Authentic Nigerian Pidgin communication with local slang
- **Human-Centric Design**: Feels like trading with a real person ("The Plug")
- **Natural Language Understanding**: Recognizes casual commands like "buy", "rates", "how far"

### 🛡️ Security & Reliability

- **Double-Confirmation**: Critical data (wallet addresses, bank accounts) requires two-entry verification
- **Stateless Architecture**: No internal balance holding reduces risk exposure
- **Immutable Ledger**: Neon PostgreSQL ensures permanent transaction records
- **Idempotent Operations**: Admin actions prevent double-crediting or duplicate notifications
- **Error Resilience**: Comprehensive logging and graceful error handling

### ⚙️ Operational Efficiency

- **Real-Time Rates**: Dynamic USDT/NGN exchange rates updatable via admin commands
- **Automated Reminders**: Smart engagement messages every 90 days
- **One-Click Approvals**: Inline buttons for admin trade fulfillment
- **Broadcast Messaging**: Reach all users with system announcements
- **Transaction History**: Per-user ledger of all trades

### 📱 Multi-Platform Support

- **Telegram Native**: Full support for photos, documents, and rich formatting
- **Cloud Deployable**: Works on Render, Koyeb, Railway with minimal configuration
- **Containerizable**: Ready for Docker deployment

---

## System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Users                       │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│           Telegram Bot API (python-telegram-bot)        │
│   • ConversationHandler (state management)              │
│   • MessageHandler / CallbackQueryHandler               │
│   • Error handling & logging                            │
└────────────────────────────┬────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
        ┌─────────────────┐      ┌──────────────────┐
        │  Database Layer │      │  Blockchain      │
        │  (Neon)         │      │  (TronGrid API)  │
        │  • Users        │      │  • USDT balance  │
        │  • Transactions │      │  • TX verify     │
        │  • Settings     │      │  • Monitor       │
        └─────────────────┘      └──────────────────┘
```

### Conversation Flow

**Buy USDT (NGN → Crypto)**:
```
START → Amount → Wallet → Confirm Wallet → Payment Proof → Admin Approval → END
```

**Sell USDT (Crypto → NGN)**:
```
START → Amount → Bank Details → Confirm Account → TX Hash → Admin Approval → END
```

### Data Model

**Users Table**
- `user_id` (Telegram ID) - Primary key
- `phone`, `bank_name`, `bank_account_name`, `bank_account_number`, `crypto_address`
- `naira_balance`, `usdt_balance` (for balance tracking if needed)
- `created_at` (audit timestamp)

**Transactions Table**
- `id` - Auto-generated transaction ID
- `user_id` - Linked user
- `type` (buy/sell/deposit)
- `amount_currency`, `amount`, `rate`
- `status` (pending/completed/failed)
- `tx_hash` (blockchain hash if applicable)
- `details` (metadata)
- `created_at` (audit timestamp)

**Settings Table**
- `key` - Setting name (buy_rate, sell_rate, etc)
- `value` - Setting value

---

## Installation & Deployment

### Local Development

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or: venv\Scripts\activate (Windows)
   pip install -r requirements.txt
   ```

2. **Configure Database**
   - Create Neon project: https://neon.tech
   - Run `migrations/002_full_neon_schema.sql` in Neon SQL editor
   - Get connection string from Neon dashboard

3. **Create `.env` File**
   ```bash
   cp .env.example .env
   # Edit with your credentials
   ```

4. **Run Locally**
   ```bash
   python bot.py
   ```

### Production Deployment (Render)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push -u origin main
   ```

2. **Create Render Service**
   - Visit https://render.com
   - Create new "Web Service"
   - Connect GitHub repository
   - Use these settings:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python bot.py`
     - **Environment**: Add variables from `.env`

3. **Configure Environment Variables**
   In Render dashboard, add all variables from `.env.example`

4. **Deploy**
   - Render auto-deploys on GitHub push
   - Monitor logs in Render dashboard

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENV PORT=8080
CMD ["python", "bot.py"]
```

Build and run:
```bash
docker build -t crypto-bot .
docker run -p 8080:8080 --env-file .env crypto-bot
```

---

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `BOT_TOKEN` | ✅ | Telegram bot token from BotFather | `123456789:ABCdefGHI...` |
| `ADMIN_ID` | ✅ | Your Telegram user ID (admin) | `987654321` |
| `DATABASE_URL` | ✅ | Neon PostgreSQL connection string | `postgresql://user:pass@ep-xxx.neon.tech/neondb` |
| `YOUR_USDT_WALLET` | ✅ | Your TRC20 USDT wallet | `TR7NHqjeKQx...` |
| `YOUR_BANK_NAME` | ✅ | Bank name shown to users | `Moniepoint` |
| `YOUR_BANK_ACCOUNT` | ✅ | 10-digit bank account | `0123456789` |
| `YOUR_BANK_ACCOUNT_NAME` | ✅ | Account holder name | `Business Name` |
| `TRONGRID_API_KEY` | ⚠️ | TronGrid API key (optional, recommended) | `f9a0...` |
| `PAYSTACK_SECRET_KEY` | ⚠️ | Paystack integration (optional) | `sk_live_...` |

---

## Usage

### User Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize and show welcome message |
| `buy` or `/buy` | Start buying USDT |
| `sell` or `/sell` | Start selling USDT |
| `rates` or `price` | Show current USDT/NGN rates |
| `history` | View your recent transactions |
| `support` | Contact admin for help |
| `cancel` | Cancel current trade |

### Admin Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `/setrate` | `/setrate <buy> <sell>` | Update exchange rates (NGN/USDT) |
| `/broadcast` | `/broadcast <message>` | Send announcement to all users |

**Example**:
```
/setrate 1450 1550
# Sets: Buy rate = ₦1,450/USDT, Sell rate = ₦1,550/USDT
```

### Transaction Flow

**Buying USDT (Customer)**:
1. User enters: `buy`
2. Bot asks: "How much USDT?"
3. User enters amount: `100`
4. Bot asks: "What's your TRC20 wallet?"
5. User provides wallet
6. Bot asks: "Confirm wallet address" (security)
7. Bot shows bank details and asks for payment proof
8. User uploads screenshot of payment
9. Bot notifies admin
10. Admin approves → Bot sends USDT

**Selling USDT (Customer)**:
1. User enters: `sell`
2. Bot asks: "How much USDT?"
3. User enters amount: `100`
4. Bot asks: "Bank details?" (Bank, Account, Name)
5. Bot asks: "Confirm account number"
6. Bot shows merchant USDT wallet address
7. User sends ₦ equivalent in USDT
8. User provides blockchain transaction ID
9. Bot notifies admin
10. Admin approves → Bot sends Naira

---

## Administration

### Managing Trades

When a user initiates a trade, the admin receives a notification with two buttons:
- ✅ **Approved (Credit User)** - Marks trade as complete and notifies user
- ❌ **Reject (Wait)** - Marks as pending (funds haven't arrived)

### Updating Rates

```
/setrate 1450 1550
```
- `1450` = Buy rate (customer sells to bot)
- `1550` = Sell rate (customer buys from bot)

### Broadcasting Messages

```
/broadcast Happy New Year! Use code NEWYEAR for 5% bonus
```
Sends to all registered users.

---

## Project Structure

```
crypto_exchange_bot/
├── .env.example              # Example environment variables
├── .gitignore                # Git exclusions
├── requirements.txt          # Python dependencies
├── render.yaml               # Render.com configuration
├── start.sh                  # Start script for deployment
│
├── bot.py                    # Main bot logic (300+ lines)
│   ├── Infrastructure (health check server)
│   ├── Security (admin validation)
│   ├── Core commands (start, rates, history)
│   ├── Buy conversation flow
│   ├── Sell conversation flow
│   ├── Admin fulfillment
│   ├── Broadcasting & scheduling
│   └── Main app initialization
│
├── config.py                 # Configuration management
│   ├── Environment loading
│   ├── Telegram settings
│   ├── Database credentials
│   ├── Blockchain settings
│   └── Merchant bank details
│
├── database.py               # Neon PostgreSQL abstraction layer
│   ├── User management
│   ├── Transaction recording
│   ├── Settings persistence
│   ├── Session persistence
│   ├── Ban system
│   └── Query helpers
│
├── responses.py              # Human-like response library
│   └── 200+ variations in Nigerian Pidgin
│
├── middleware/                # Cross-cutting concerns
│   └── rate_limiter.py       # Rate limiting / anti-spam
│
├── adapters/                 # Platform-specific I/O
│   └── telegram_adapter.py   # Telegram adapter
│
├── utils/                    # Utility packages
│   ├── bank_utils.py         # NGN transaction utilities
│   └── tron_utils.py         # Blockchain utilities
│
└── migrations/               # SQL migration files
    ├── 001_add_sessions_and_bans.sql
    └── 002_full_neon_schema.sql
```

---

## Development

### Code Style

- **PEP 8**: Follow Python Enhancement Proposal 8
- **Type Hints**: All functions should have type annotations
- **Docstrings**: Use Google-style docstrings
- **Logging**: Use `logger` for all messages

### Adding New Features

1. Create a new function with clear purpose
2. Add comprehensive docstring
3. Add type hints
4. Add error handling and logging
5. Test locally
6. Commit with descriptive message

### Testing

Currently, manual testing via Telegram is recommended. Future: Add automated test suite.

---

## Security

### Security Considerations

1. **Never Commit `.env`**: Always use `.env.example`
2. **Private Keys**: Never store private keys in code
3. **USDT Sending**: Currently disabled for manual fulfillment (safer)
4. **Double-Verification**: All payments require confirmation
5. **Audit Trail**: All transactions logged permanently
6. **Admin Validation**: All admin actions checked against `ADMIN_IDS`

### Production Security Checklist

- ✅ Set `ADMIN_ID` to your user ID only
- ✅ Use strong `DATABASE_URL` (keep it secret)
- ✅ Use HTTPS-only (Render provides this by default)
- ✅ Regularly rotate API keys
- ✅ Monitor logs for suspicious activity
- ✅ Implement 2FA for Neon and Telegram

---

## Troubleshooting

### Bot Not Responding

**Check**:
1. `BOT_TOKEN` is correct (from BotFather)
2. `python bot.py` runs without errors
3. Internet connection active
4. Logs in terminal for error messages

### Database Errors

**Check**:
1. `DATABASE_URL` is correct
2. Tables are created (run migration SQL)
3. Neon project is active (not paused)

### Blockchain Verification Fails

**Check**:
1. `YOUR_USDT_WALLET` is correct format (starts with T)
2. Transaction actually sent to wallet (check TronScan)
3. `TRONGRID_API_KEY` is set (optional but recommended)
4. Network connectivity

### "Permission Denied" for Admin Commands

**Check**:
1. Your Telegram user ID matches `ADMIN_ID`
2. Get your ID from [@userinfobot](https://t.me/userinfobot)

### Rate Limiting / Slow Responses

**Fix**:
1. Render free tier may have slower performance
2. Upgrade to paid tier or use alternative hosting
3. Implement caching if rates updated frequently

---

## License

MIT License - See LICENSE file for details

---

## Support & Contact

- **Technical Issues**: Open an issue on GitHub
- **Feature Requests**: Discuss in Discussions tab
- **In-App Support**: Users can type `/support` for admin contact

---

**Built with 💚 for the Nigerian Crypto Community**

*Last Updated: June 2026*