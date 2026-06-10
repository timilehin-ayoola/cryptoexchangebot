# API Reference

Complete reference for all modules and functions in the crypto exchange bot.

## Table of Contents

1. [config.py](#configpy)
2. [database.py](#databasepy)
3. [responses.py](#responsespy)
4. [utils/tron_utils.py](#utilstron_utilspy)
5. [utils/bank_utils.py](#utilsbank_utilspy)
6. [bot.py](#botpy)

---

## config.py

Configuration and environment variable management.

### Functions

#### `get_env(key: str, default: Optional[str] = None, required: bool = False) -> str`

Safely retrieve environment variable with optional default.

**Parameters:**
- `key` (str): Environment variable name
- `default` (Optional[str]): Default value if not found
- `required` (bool): If True, warns if missing

**Returns:** Environment variable value or default

**Example:**
```python
api_key = get_env("TRONGRID_API_KEY", required=False)
```

### Constants

| Name | Type | Description |
|------|------|-------------|
| `BOT_TOKEN` | str | Telegram bot API token |
| `ADMIN_IDS` | List[int] | List of admin user IDs |
| `DATABASE_URL` | str | Neon PostgreSQL connection string |
| `YOUR_USDT_WALLET` | str | Merchant USDT wallet address |
| `YOUR_BANK_NAME` | str | Bank name for settlements |
| `YOUR_BANK_ACCOUNT` | str | 10-digit bank account |
| `YOUR_BANK_ACCOUNT_NAME` | str | Account holder name |
| `DEFAULT_BUY_RATE` | int | Default buy rate (NGN/USDT) |
| `DEFAULT_SELL_RATE` | int | Default sell rate (NGN/USDT) |

---

## database.py

Neon PostgreSQL abstraction layer for data persistence.

### User Management

#### `get_user(user_id: int) -> Optional[Dict[str, Any]]`

Retrieve user profile from database.

**Parameters:**
- `user_id` (int): Telegram user ID

**Returns:** User dictionary or None if not found

**Example:**
```python
user = get_user(123456789)
if user:
    print(f"User phone: {user['phone']}")
```

---

#### `register_user(user_id: int, phone: str, bank_name: str, bank_account_name: str, bank_account_number: str, crypto_address: str) -> None`

Register or update user profile (UPSERT operation).

**Parameters:**
- `user_id` (int): Telegram user ID
- `phone` (str): Contact phone number
- `bank_name` (str): Bank name
- `bank_account_name` (str): Account holder name
- `bank_account_number` (str): 10-digit account number
- `crypto_address` (str): TRC20 wallet address

**Example:**
```python
register_user(
    user_id=123456789,
    phone="+234 800 1234567",
    bank_name="Access Bank",
    bank_account_name="John Doe",
    bank_account_number="0123456789",
    crypto_address="TR7NHqjeKQx..."
)
```

---

#### `auto_create_user(user_id: int) -> Dict[str, Any]`

Ensure user exists, creating blank profile if necessary.

**Parameters:**
- `user_id` (int): Telegram user ID

**Returns:** User dictionary (empty if creation failed)

---

#### `update_balance(user_id: int, naira_delta: float = 0.0, usdt_delta: float = 0.0) -> None`

Update user's internal balance.

**Parameters:**
- `user_id` (int): User ID
- `naira_delta` (float): Amount to add/subtract from Naira
- `usdt_delta` (float): Amount to add/subtract from USDT

---

### Transaction Management

#### `add_transaction(user_id: int, tx_type: str, amount_currency: str, amount: float, rate: float, status: str, tx_hash: Optional[str] = None, details: Optional[str] = None) -> Optional[int]`

Record a new transaction in the ledger.

**Parameters:**
- `user_id` (int): User initiating transaction
- `tx_type` (str): Type ('buy', 'sell', 'deposit')
- `amount_currency` (str): Currency ('USDT', 'NGN')
- `amount` (float): Transaction amount
- `rate` (float): Exchange rate used
- `status` (str): Status ('pending', 'completed', 'failed')
- `tx_hash` (Optional[str]): Blockchain hash if applicable
- `details` (Optional[str]): Metadata/notes

**Returns:** Transaction ID (int) or None if failed

**Example:**
```python
tx_id = add_transaction(
    user_id=123456789,
    tx_type='buy',
    amount_currency='USDT',
    amount=100,
    rate=1500,
    status='pending',
    details="Recipient: TR7NHqjeKQx..."
)
```

---

#### `update_transaction_status(tx_id: int, status: str) -> None`

Update status of existing transaction.

**Parameters:**
- `tx_id` (int): Transaction ID
- `status` (str): New status

---

#### `get_transaction(tx_id: int) -> Optional[Dict[str, Any]]`

Retrieve transaction details by ID.

**Parameters:**
- `tx_id` (int): Transaction ID

**Returns:** Transaction dictionary or None

---

#### `get_user_transactions(user_id: int, limit: int = 10) -> List[Dict[str, Any]]`

Get most recent transactions for a user.

**Parameters:**
- `user_id` (int): User ID
- `limit` (int): Maximum records to return (default 10)

**Returns:** List of transaction dictionaries

---

### Settings Management

#### `get_setting(key: str) -> Optional[str]`

Retrieve system setting value.

**Parameters:**
- `key` (str): Setting name (e.g., 'buy_rate')

**Returns:** Setting value as string or None

**Example:**
```python
buy_rate = int(get_setting('buy_rate') or 1480)
```

---

#### `set_setting(key: str, value: str) -> None`

Update or create system setting.

**Parameters:**
- `key` (str): Setting name
- `value` (str): Setting value

**Example:**
```python
set_setting('buy_rate', '1450')
```

---

#### `get_all_users() -> List[int]`

Get list of all registered user IDs.

**Returns:** List of Telegram user IDs

---

### Initialization

#### `init_db() -> None`

Initialize database with default settings. Call on bot startup.

---

## responses.py

Response templates in Nigerian Pidgin English.

### Constants

#### `RESPONSES: Dict[str, List[str]]`

Dictionary of response variations by category.

**Categories:**
- `WELCOME`: Welcome message variations (10+)
- `RATES_HEADER`: Exchange rate display headers
- `BUY_START`: Starting buy conversation
- `BUY_AMOUNT_SUCCESS`: Confirmation after amount entered
- `BUY_WALLET_INVALID`: Invalid wallet format
- `BUY_PAYMENT_DETAILS`: Payment instructions
- `SELL_START`: Starting sell conversation
- `INVALID_AMOUNT`: Invalid amount input
- `ADMIN_APPROVE_USER`: Admin approval notification
- `ADMIN_REJECT_USER`: Admin rejection notification
- And many more...

### Functions

#### `get_text(key: str, **kwargs: Any) -> str`

Get random response variation with formatted parameters.

**Parameters:**
- `key` (str): Response category key
- `**kwargs`: Placeholders to format (amount=100, naira=1500000, etc)

**Returns:** Formatted response string

**Examples:**
```python
# Basic response
msg = get_text("WELCOME")
# Result: "How far! 🏦 Welcome to the P2P Exchange..."

# With parameters
msg = get_text("BUY_AMOUNT_SUCCESS", amount=50)
# Result: "Got it! 50 USDT. ✅ Now, where I go send am?"

# In handler
await update.message.reply_text(get_text("BUY_START"))
```

---

## utils/tron_utils.py

TRON blockchain utilities for USDT (TRC20) operations.

### Constants

| Name | Value | Description |
|------|-------|-------------|
| `USDT_CONTRACT` | `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` | Official USDT contract address |
| `TRON_API_BASE` | `https://api.trongrid.io/v1` | TronGrid API base URL |
| `REQUEST_TIMEOUT` | `10` | Request timeout in seconds |
| `POLLING_INTERVAL` | `15` | Polling interval in seconds |

### Functions

#### `get_usdt_balance(address: str) -> float`

Query USDT balance of a TRC20 address.

**Parameters:**
- `address` (str): TRC20 wallet address (format: T...)

**Returns:** USDT balance as float

**Example:**
```python
balance = get_usdt_balance("TR7NHqjeKQx...")
print(f"Balance: {balance} USDT")
```

---

#### `monitor_incoming_usdt(expected_amount: float, timeout_seconds: int = 300) -> Tuple[Optional[str], Optional[str], Optional[float]]`

Poll blockchain for incoming USDT transfer.

**Parameters:**
- `expected_amount` (float): Amount to look for
- `timeout_seconds` (int): Maximum polling time (default 300)

**Returns:** Tuple of (tx_id, sender_address, actual_amount) or (None, None, None)

**Example:**
```python
tx_id, sender, amount = monitor_incoming_usdt(100, timeout_seconds=300)
if tx_id:
    print(f"Received {amount} USDT from {sender}")
```

---

#### `verify_transaction(tx_hash: str) -> Optional[Dict[str, Any]]`

Get full transaction metadata from blockchain.

**Parameters:**
- `tx_hash` (str): Transaction ID

**Returns:** Transaction dictionary or None

---

#### `verify_usdt_deposit(tx_hash: str, expected_amount: float) -> Tuple[Optional[str], Optional[float]]`

Validate USDT deposit by checking blockchain history.

**Parameters:**
- `tx_hash` (str): Transaction ID to verify
- `expected_amount` (float): Expected USDT amount

**Returns:** Tuple of (sender_address, actual_amount) or (None, None)

**Example:**
```python
sender, amount = verify_usdt_deposit(tx_hash, expected_amount=100)
if sender:
    print(f"Verified: {amount} USDT from {sender}")
```

---

#### `send_usdt(to_address: str, amount_usdt: float, private_key: str) -> str`

**Status**: ⚠️ **NOT IMPLEMENTED** (template only)

Sends USDT from merchant wallet. Currently raises `NotImplementedError`.

Requires integration with tronpy or similar signing library.

---

## utils/bank_utils.py

Nigerian Naira bank transaction utilities.

### Functions

#### `simulate_bank_deposit(user_id: int, amount_ngn: float) -> bool`

Simulate bank deposit for testing (development).

**Parameters:**
- `user_id` (int): User ID to credit
- `amount_ngn` (float): Amount in Naira

**Returns:** True if successful, False otherwise

**Note:** In production, use actual payment webhooks (Paystack, Monnify)

---

#### `paystack_verify_payment(reference: str) -> Optional[Dict[str, Any]]`

**Status**: 🚫 **NOT IMPLEMENTED** (template)

Verify Paystack payment by reference.

**Parameters:**
- `reference` (str): Paystack transaction reference

**Returns:** Payment details dictionary or None

**Note:** Requires PAYSTACK_SECRET_KEY configuration

---

#### `setup_paystack_webhook() -> None`

Documentation function for Paystack webhook setup.

See function docstring for integration steps.

---

## bot.py

Main bot application and conversation flows.

### State Constants

Conversation states for multi-step dialogs:
```python
(
    BUY_AMOUNT,           # User entering purchase amount
    BUY_WALLET,           # User entering TRC20 wallet
    BUY_CONFIRM_WALLET,   # User confirming wallet (security)
    BUY_PAYMENT_PROOF,    # User uploading payment proof
    SELL_AMOUNT,          # User entering USDT amount
    SELL_BANK_DETAILS,    # User entering bank details
    SELL_CONFIRM_ACC,     # User confirming account (security)
    SELL_TX_HASH,         # User entering blockchain hash
) = range(8)
```

### Security

#### `is_admin(user_id: int) -> bool`

Check if user has admin privileges.

**Parameters:**
- `user_id` (int): Telegram user ID

**Returns:** True if user ID in ADMIN_IDS list

---

### Command Handlers

#### `start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`

Start command - initializes user profile and shows welcome.

---

#### `rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`

Show current USDT/NGN exchange rates from database.

---

#### `history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`

Display user's recent transaction history (10 transactions).

---

#### `support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`

Provide admin contact link for support.

---

#### `setrate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`

**Admin Command**: Update exchange rates

**Usage**: `/setrate 1450 1550`
- First value: Buy rate (NGN/USDT)
- Second value: Sell rate (NGN/USDT)

---

#### `broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`

**Admin Command**: Send announcement to all users

**Usage**: `/broadcast Your message here`

---

### Buy Conversation

#### `buy_start(update, context) -> int`
Entry point for buying USDT

#### `buy_amount(update, context) -> int`
Validate and record purchase amount

#### `buy_wallet(update, context) -> int`
Collect and validate TRC20 wallet address

#### `buy_confirm_wallet(update, context) -> int`
Double-verify wallet address

#### `buy_payment_proof(update, context) -> int`
Accept payment proof and notify admin

### Sell Conversation

#### `sell_start(update, context) -> int`
Entry point for selling USDT

#### `sell_amount(update, context) -> int`
Validate and record USDT amount

#### `sell_bank_details(update, context) -> int`
Collect bank details for payment

#### `sell_confirm_acc(update, context) -> int`
Double-verify account number

#### `sell_tx_hash(update, context) -> int`
Accept blockchain transaction hash and notify admin

---

### Admin Fulfillment

#### `handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`

Handle admin approval/rejection of trades via inline buttons.

Prevents double-crediting with idempotency checks.

---

### Scheduling

#### `reminder_scheduler(app: Application) -> NoReturn`

Background loop for periodic user engagement reminders (every 90 days).

---

### Infrastructure

#### `run_dummy_server() -> None`

Start background HTTP server for health checks (required for Render).

#### `HealthCheckHandler`

Minimal HTTP handler responding to health checks.

---

### Application Initialization

#### `main() -> None`

Orchestrates bot initialization:
1. Starts health check server
2. Creates Application
3. Registers all handlers
4. Starts polling

**Call this**: `if __name__ == "__main__": main()`

---

## Error Handling

All functions include:
- Try-except blocks for resilience
- Logging of errors with context
- Graceful degradation (returns None/False rather than crashing)
- User-friendly error messages

---

## Best Practices

### Using Database Functions

```python
# Always check for None
user = get_user(user_id)
if user:
    print(user['phone'])
else:
    logger.warning(f"User not found: {user_id}")
```

### Using Response Functions

```python
# Always use format parameters for dynamic content
msg = get_text("BUY_AMOUNT_SUCCESS", amount=amount)
await update.message.reply_text(msg, parse_mode="Markdown")
```

### Using Blockchain Functions

```python
# Handle blockchain query failures gracefully
balance = get_usdt_balance(address)
if balance > 0:
    # Blockchain query succeeded
    pass
else:
    # Could mean 0 balance OR API failure
    logger.error(f"Could not verify balance for {address}")
```

---

For more information, see README.md and individual module docstrings.
