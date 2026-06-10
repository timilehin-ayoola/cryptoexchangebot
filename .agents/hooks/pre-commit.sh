#!/usr/bin/env bash
# Pre-commit hook for bot_cryptoexchangebot
# Place in .git/hooks/pre-commit (chmod +x)

set -e

echo "🔍 Pre-commit checks running..."

# 1. Check for hardcoded secrets
if grep -rn "sk_\|pk_\|private_key.*=" --include="*.py" . \
   | grep -v "__pycache__" \
   | grep -v ".env" \
   | grep -v "example" \
   | grep -v "test_"; then
    echo "❌ FAIL: Hardcoded secrets found! Use environment variables."
    exit 1
fi

# 2. Check for Telegram imports in engine.py
if grep -n "from telegram" engine.py 2>/dev/null; then
    echo "❌ FAIL: engine.py must not import Telegram (adapter pattern violation)."
    exit 1
fi

# 3. Check engine.py line count
ENGINE_LINES=$(wc -l < engine.py)
if [ "$ENGINE_LINES" -gt 1000 ]; then
    echo "❌ FAIL: engine.py has $ENGINE_LINES lines (max 1000). Split into modules."
    exit 1
fi

# 4. Run tests
echo "🧪 Running tests..."
if ! python -m pytest tests/ -v --tb=short 2>&1; then
    echo "❌ FAIL: Tests failed. Fix before committing."
    exit 1
fi

echo "✅ All pre-commit checks passed."
