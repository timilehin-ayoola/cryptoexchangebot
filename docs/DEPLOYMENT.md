# Deployment Guide

Complete guide for deploying the Nigerian P2P Crypto Exchange Bot to production.

## Quick Links

- [Local Development](#local-development)
- [Render Deployment](#render-deployment)
- [Docker Deployment](#docker-deployment)
- [Database Setup](#database-setup)
- [Environment Variables](#environment-variables)
- [Monitoring & Logs](#monitoring--logs)

---

## Local Development

### Prerequisites

- Python 3.10+
- Git
- Text editor (VS Code recommended)

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/crypto_exchange_bot.git
cd crypto_exchange_bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or open in your editor

# Run the bot
python bot.py
```

### Testing in Telegram

1. Open your test bot on Telegram
2. Type `/start` to initialize
3. Try `/help` to see commands
4. Test `/buy` and `/sell` flows
5. As admin, test `/setrate 1450 1550`

---

## Render Deployment

### Prerequisites

- GitHub account
- GitHub repository (public or private)
- Render account (free tier available)

### Step 1: Prepare Repository

```bash
# Ensure all files are committed
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Create Render Service

1. Go to https://render.com
2. Sign up or log in
3. Dashboard → New +
4. Select "Web Service"
5. Connect your GitHub repository
6. Name: `crypto-exchange-bot` (or your choice)

### Step 3: Configure Service

**Build & Deploy Settings:**
```
Build Command: pip install -r requirements.txt
Start Command: python bot.py
```

**Environment:**
- Plan: Free (0.5 CPU, 0.5 GB RAM, sleeps after 15 min inactivity)
  - For production: Choose Starter/Pro plan

**Auto-Deploy**: Toggle ON (auto-deploy on git push)

### Step 4: Add Environment Variables

In Render dashboard → Environment:

```
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_id
DATABASE_URL=postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb
TRONGRID_API_KEY=your_trongrid_key
YOUR_USDT_WALLET=TR7NHq...
YOUR_BANK_NAME=Your Bank
YOUR_BANK_ACCOUNT=0123456789
YOUR_BANK_ACCOUNT_NAME=Your Name
```

### Step 5: Deploy

- Click "Create Web Service"
- Render builds and deploys automatically
- Monitor logs in dashboard

**First deployment** takes 2-3 minutes.

### Monitoring

- Logs tab: Real-time application logs
- Metrics tab: CPU, RAM, requests
- Events tab: Deployment history

### Free Tier Limitations

- **Sleeps after 15 min inactivity**: Bot won't respond while sleeping
  - **Solution**: Keep-alive service (external)
  - **Better**: Upgrade to Starter plan ($5/month)

- **No persistent disk**: Database is on Neon (cloud), so no problem
- **Limited resources**: Suitable for small-medium usage

### Upgrading from Free to Pro

1. Dashboard → Settings
2. Plan → Starter ($7/month) or Pro ($12/month)
3. Change resource allocation
4. Render restarts service with new resources

---

## Docker Deployment

### Build Docker Image

**Create `Dockerfile`:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080')" || exit 1

# Run bot
CMD ["python", "bot.py"]
```

**Create `.dockerignore`:**
```
.env
.git
.gitignore
__pycache__
*.pyc
.venv
venv
.vscode
.DS_Store
.pytest_cache
```

### Build & Run Locally

```bash
# Build image
docker build -t crypto-bot:latest .

# Run container
docker run --env-file .env -p 8080:8080 crypto-bot:latest

# Run in background
docker run -d --env-file .env -p 8080:8080 --name crypto-bot crypto-bot:latest

# View logs
docker logs -f crypto-bot

# Stop container
docker stop crypto-bot

# Remove container
docker rm crypto-bot
```

### Deploy to Docker Hub

```bash
# Tag image
docker tag crypto-bot:latest yourusername/crypto-bot:latest

# Push to Docker Hub
docker push yourusername/crypto-bot:latest

# Others can run:
docker run --env-file .env yourusername/crypto-bot:latest
```

### Deploy to Cloud Services

**Google Cloud Run:**
```bash
gcloud run deploy crypto-bot \
    --image yourusername/crypto-bot:latest \
    --set-env-vars BOT_TOKEN=$BOT_TOKEN \
    --memory 512Mi \
    --timeout 3600
```

**AWS ECS:**
- Create ECR repository
- Push Docker image to ECR
- Create ECS task definition
- Launch Fargate service

**DigitalOcean App Platform:**
- Connect GitHub repository
- Configure build (Dockerfile)
- Add environment variables
- Deploy

---

## Database Setup

### Create Neon Project

1. Visit https://neon.tech
2. Sign up or log in (GitHub OAuth available)
3. Create a new project
   - Name: `crypto-bot-prod` (or your choice)
   - Region: Closest to target users
4. Create project (takes ~10 seconds)

### Get Connection String

In Neon dashboard:
- Go to **Connection Details**
- Copy the connection string (starts with `postgresql://`)
- It looks like: `postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb`

### Run Database Schema

Run the migration file in Neon SQL Editor:

```bash
# Option 1: Copy and paste from migrations/002_full_neon_schema.sql
# Option 2: Use psql CLI
psql "postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb" -f migrations/002_full_neon_schema.sql
```

The schema creates these tables:
- **users** - User profiles and balances
- **transactions** - Trade history with audit trail
- **settings** - System-wide configuration
- **user_sessions** - In-progress conversations (survives restarts)
- **bans** - Abusive user tracking

### Migrating from Supabase

If you have existing data in Supabase:

1. Export data from Supabase (Table Editor → Export)
2. Import into Neon (Neon SQL Editor → Import CSV)
3. Update `DATABASE_URL` in your environment
4. Deploy the migrated code

---

## Environment Variables

### Required Variables

| Variable | Example | Notes |
|----------|---------|-------|
| `BOT_TOKEN` | `12345:ABCdef...` | From @BotFather on Telegram |
| `ADMIN_ID` | `987654321` | Get from @userinfobot |
| `DATABASE_URL` | `postgresql://user:pass@ep-xxx.neon.tech/neondb` | From Neon dashboard |

### Recommended Variables

| Variable | Example | Notes |
|----------|---------|-------|
| `TRONGRID_API_KEY` | `f9a0...` | From trongrid.io (optional but recommended) |
| `YOUR_USDT_WALLET` | `TR7NHq...` | Your TRC20 USDT wallet |

### Optional Variables

| Variable | Notes |
|----------|-------|
| `YOUR_BANK_NAME` | Your bank name (shown to users) |
| `YOUR_BANK_ACCOUNT` | Your bank account number |
| `YOUR_BANK_ACCOUNT_NAME` | Account holder name |
| `PAYSTACK_SECRET_KEY` | For Paystack integration |

---

## Monitoring & Logs

### Render Logs

- Dashboard → Logs tab
- Real-time streaming
- Search and filter available

### Application Logging

The bot logs to stdout/stderr:
- **INFO**: Normal operations
- **ERROR**: Issues that need attention
- **CRITICAL**: Severe system failures

### Key Metrics to Monitor

- **Bot responsiveness**: User commands being processed
- **Database connections**: Neon queries succeeding
- **Error rates**: Check for repeated errors
- **Blockchain connectivity**: TronGrid API health
- **Admin approvals**: Ensure fulfillment is happening

### Setting Up Alerts

**Render Alerts:**
- Settings → Notifications
- Enable: Failed deploys, restart events

**Third-party Monitoring:**
- Use Sentry for error tracking
- Use New Relic for performance monitoring
- Use Datadog for comprehensive monitoring

---

## Troubleshooting Deployments

### Bot Not Responding

```bash
# Check Render logs for errors
# Common causes:
# 1. BOT_TOKEN invalid or expired
# 2. Database credentials wrong
# 3. Service crashed (check error logs)
```

### Database Connection Failed

```
Error: "DATABASE_URL must be set"

Solution:
- Check environment variables in Render dashboard
- Verify they match Neon connection string exactly
- Test locally with .env file first
```

### Memory Issues on Free Tier

```
Service keeps sleeping or crashing

Solutions:
1. Use keep-alive service (external pinger)
2. Upgrade to Starter plan (recommended)
3. Optimize code to use less memory
```

### Blockchain Verification Fails

```
Error: "Failed to fetch USDT balance"

Solutions:
1. Add TRONGRID_API_KEY to environment
2. Check internet connectivity
3. Verify wallet address format (starts with T)
4. Check TronGrid API status: https://status.trongrid.io
```

---

## Production Checklist

- [ ] Environment variables set correctly
- [ ] Database schema created and tested
- [ ] .env file NOT committed to git
- [ ] Admin ID set to your user ID only
- [ ] USDT wallet address verified
- [ ] Bank details configured
- [ ] Bot commands tested in Telegram
- [ ] Admin `/setrate` command works
- [ ] Error logging enabled
- [ ] Backup plan for data recovery
- [ ] Regular security audits scheduled

---

## Scaling to Production

### Free Tier → Starter Plan

1. Render: Change plan ($7/month) for always-on service
2. Neon: Upgrade if >0.5GB data expected (free tier: 0.5GB)
3. TronGrid: Consider paid API key for rate limits

### Adding Load Balancing

If bot gets 1000+ concurrent users:
1. Use Render Professional plan
2. Enable auto-scaling
3. Monitor performance metrics

### Database Optimization

```sql
-- Add indexes for frequently queried fields
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- Archive old transactions (optional)
CREATE TABLE transactions_archive AS 
SELECT * FROM transactions 
WHERE created_at < NOW() - INTERVAL '1 year';

DELETE FROM transactions 
WHERE created_at < NOW() - INTERVAL '1 year';
```

---

For questions, check the main README or open a GitHub issue.