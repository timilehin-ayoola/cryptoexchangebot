# Quick Reference Guide

**A 5-minute guide to understand the entire codebase.**

## 📚 Start Here (In This Order)

### 1️⃣ **README.md** (5 min read)
Get the big picture: what the bot does, features, and architecture overview.
- ✅ What is this project?
- ✅ Key features
- ✅ System architecture
- ✅ Quick start

### 2️⃣ **REPOSITORY_OVERVIEW.md** (3 min read)
Professional improvements made and file structure.
- ✅ What changed?
- ✅ File organization
- ✅ Quality improvements

### 3️⃣ **API_REFERENCE.md** (lookup as needed)
Function reference for developers.
- 🔍 How to use database functions?
- 🔍 What blockchain functions are available?
- 🔍 How to add responses?

---

## 🎯 Key Concepts

### Three Main Transaction Types

1. **Buy USDT** (Customer → Bot: NGN → USDT)
   - Customer pays NGN to merchant bank
   - Customer receives USDT to their wallet

2. **Sell USDT** (Customer → Bot: USDT → NGN)
   - Customer sends USDT to merchant wallet
   - Customer receives NGN to their bank account

3. **Admin Fulfillment**
   - Admin approves trades after verification
   - Bot notifies customer

### Four Core Modules

```
┌─────────────────────────────────────────┐
│  bot.py                                 │
│  • Telegram handlers                    │
│  • Conversation flows                   │
│  • Admin commands                       │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
┌──────────────┐ ┌────────────┐ ┌────────────┐
│ database.py  │ │ config.py  │ │ responses.│
│ • Users      │ │ • Settings │ │ py        │
│ • Trades     │ │ • Secrets  │ │ • 200+    │
│ • History    │ │ • Creds    │ │   messages│
└──────────────┘ └────────────┘ └────────────┘
        ▼                          
    utils/                    
    ├── tron_utils.py (Blockchain)
    └── bank_utils.py (Payments)
```

---

## 📁 File Quick Reference

| File | Purpose | Key Classes/Functions | Size |
|------|---------|----------------------|------|
| **bot.py** | Main app entry | `start()`, `buy_start()`, `sell_start()` | 1200 lines |
| **config.py** | Settings | `get_env()`, constants | 120 lines |
| **database.py** | Data layer | `get_user()`, `add_transaction()` | 350 lines |
| **responses.py** | Messages | `get_text()`, `RESPONSES{}` | 600 lines |
| **utils/tron_utils.py** | Blockchain | `get_usdt_balance()`, `verify_transaction()` | 300 lines |
| **utils/bank_utils.py** | Payments | `simulate_bank_deposit()` | 150 lines |

---

## 🔄 Buy USDT Flow

```
User: /buy
  ↓
Bot: How much USDT?
  ↓
User: 100
  ↓
Bot: What's your wallet?
  ↓
User: TR7NHq...
  ↓
Bot: Confirm wallet (double-check)
  ↓
User: TR7NHq... (again)
  ↓
Bot: Send ₦150,000 to [bank details]
  ↓
User: [uploads payment proof]
  ↓
Bot: Notifies admin
  ↓
Admin: [clicks Approve]
  ↓
Bot: Notifies user ✅
  ↓
User: Receives 100 USDT
```

---

## 🔄 Sell USDT Flow

```
User: /sell
  ↓
Bot: How much USDT?
  ↓
User: 100
  ↓
Bot: What's your bank details?
  ↓
User: [bank, account, name]
  ↓
Bot: Confirm account number (double-check)
  ↓
User: [account number again]
  ↓
Bot: Send 100 USDT to [merchant wallet]
  ↓
User: [enters blockchain TX hash]
  ↓
Bot: Notifies admin
  ↓
Admin: [clicks Approve]
  ↓
Bot: Notifies user ✅
  ↓
User: Receives ₦150,000
```

---

## 💻 Common Tasks

### **I want to add a new command**

1. Create handler function in `bot.py`:
```python
async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler docstring"""
    await update.message.reply_text(get_text("MY_RESPONSE"))
```

2. Register in `main()`:
```python
app.add_handler(CommandHandler("mycommand", my_command))
```

3. Add response in `responses.py`:
```python
"MY_RESPONSE": [
    "Response variation 1",
    "Response variation 2",
]
```

### **I want to change exchange rates**

In Telegram (as admin):
```
/setrate 1450 1550
```

This updates the `buy_rate` and `sell_rate` in database settings.

### **I want to add a user message**

```python
# In responses.py
"MY_MESSAGE": [
    "Variation 1 🎉",
    "Variation 2 💡",
    "Variation 3 ✨",
]

# In bot.py
await update.message.reply_text(get_text("MY_MESSAGE"), parse_mode="Markdown")
```

### **I want to store user data**

```python
# In database.py (function already exists)
from database import register_user

register_user(
    user_id=update.effective_user.id,
    phone="08012345678",
    bank_name="Access Bank",
    bank_account_name="John Doe",
    bank_account_number="0123456789",
    crypto_address="TR7NHq..."
)
```

### **I want to record a transaction**

```python
# In database.py (function already exists)
from database import add_transaction

tx_id = add_transaction(
    user_id=123,
    tx_type='buy',
    amount_currency='USDT',
    amount=100,
    rate=1500,
    status='pending',
    details="User wallet: TR7NHq..."
)
```

### **I want to check blockchain**

```python
# Check balance
from utils.tron_utils import get_usdt_balance
balance = get_usdt_balance("TR7NHq...")

# Verify transaction
from utils.tron_utils import verify_transaction
tx_data = verify_transaction("tx_hash_here")
```

---

## 🔐 Security Quick Reference

### DO ✅
- Store secrets in `.env` (added to `.gitignore`)
- Use environment variables
- Validate user input
- Double-check critical data
- Log errors with context
- Use type hints
- Document security concerns

### DON'T ❌
- Commit `.env` file
- Store private keys in code
- Skip validation
- Trust user input directly
- Log passwords/secrets
- Skip error handling
- Commit credentials

---

## 🚀 Deployment Quick Reference

### Local Testing
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### Render Deployment
1. Push to GitHub
2. Create Render service
3. Add environment variables
4. Deploy!

See `DEPLOYMENT.md` for detailed steps.

---

## 📊 Database Quick Reference

### Users Table
```python
{
    'user_id': 123456789,          # Telegram ID (primary key)
    'phone': '+234 800 1234567',
    'bank_name': 'Access Bank',
    'bank_account_name': 'John Doe',
    'bank_account_number': '0123456789',
    'crypto_address': 'TR7NHq...',
    'naira_balance': 0,
    'usdt_balance': 0,
    'registered_at': '2026-05-30T...'
}
```

### Transactions Table
```python
{
    'id': 12345,                   # Auto-generated
    'user_id': 123456789,
    'type': 'buy',                 # or 'sell'
    'amount_currency': 'USDT',     # or 'NGN'
    'amount': 100,
    'rate': 1500,
    'status': 'pending',           # or 'completed', 'failed'
    'tx_hash': 'abc123...',        # Blockchain hash if applicable
    'details': 'metadata here',
    'created_at': '2026-05-30T...'
}
```

### Settings Table
```python
{
    'buy_rate': '1450',    # NGN per USDT
    'sell_rate': '1550',   # NGN per USDT
}
```

---

## 🆘 Debugging Tips

### Bot Not Responding?
1. Check `BOT_TOKEN` in environment
2. Check logs: `tail -f render.log`
3. Verify Telegram bot is registered

### Database Connection Failed?
1. Check `DATABASE_URL` is correct
2. Verify Neon project is active (not paused)
3. Check network connectivity

### Blockchain Verification Fails?
1. Verify wallet address format (starts with T)
2. Check `TRONGRID_API_KEY` is set
3. Check transaction actually exists on blockchain

### Admin Commands Not Working?
1. Verify your `ADMIN_ID` is correct
2. Get ID from @userinfobot on Telegram
3. Check admin command syntax: `/setrate 1450 1550`

---

## 📖 Documentation Map

| Need | File | Section |
|------|------|---------|
| Getting started | README.md | Quick Start |
| Deploy to production | DEPLOYMENT.md | All sections |
| API reference | API_REFERENCE.md | All sections |
| Contributing | CONTRIBUTING.md | All sections |
| What changed | PROFESSIONAL_IMPROVEMENTS.md | All sections |
| File structure | REPOSITORY_OVERVIEW.md | All sections |
| Quick reference | THIS FILE | All sections |

---

## ⚡ Key Code Snippets

### Send Message to User
```python
await context.bot.send_message(
    chat_id=user_id,
    text=get_text("RESPONSE_KEY"),
    parse_mode="Markdown"
)
```

### Create Inline Buttons
```python
keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ Approve", callback_data="action_approve"),
        InlineKeyboardButton("❌ Reject", callback_data="action_reject")
    ]
])
```

### Log Error
```python
logger.error(f"Operation failed for user {user_id}: {error}")
```

### Get Setting from Database
```python
buy_rate = int(get_setting('buy_rate') or 1480)
```

---

## 🎓 Learning Path

1. **Day 1**: Read README.md, understand features and architecture
2. **Day 2**: Run bot locally, test buy/sell flows
3. **Day 3**: Read API_REFERENCE.md for each module
4. **Day 4**: Make small changes (add response, modify message)
5. **Day 5**: Deploy to production (DEPLOYMENT.md)

---

**Ready to start? Pick a file above and dive in!** 🚀
