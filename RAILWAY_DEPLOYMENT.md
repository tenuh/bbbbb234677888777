# 🚀 Railway Deployment Guide - FIXED

## ✅ What Was Fixed

The following errors have been resolved:
1. ✅ Removed duplicate dependencies in `requirements.txt`
2. ✅ Fixed conflicting `telegram` package issue
3. ✅ Corrected `railway.toml` syntax
4. ✅ Added `.python-version` file
5. ✅ Created `nixpacks.toml` for proper build configuration

---

## Quick Deploy to Railway

### Prerequisites
1. ✅ Railway account (https://railway.app)
2. ✅ GitHub repository with your bot code
3. ✅ Telegram Bot Token from @BotFather

---

## Step-by-Step Deployment

### Step 1: Push Fixed Files to GitHub

First, push these fixed files to your GitHub repository:

```bash
git add .
git commit -m "Fix Railway deployment configuration"
git push origin main
```

### Step 2: Create Railway Project

1. Go to **https://railway.app** and sign in with GitHub
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will automatically detect it's a Python app

### Step 3: Add PostgreSQL Database

1. In your Railway project dashboard, click **"+ New"**
2. Select **"Database"**
3. Choose **"Add PostgreSQL"**
4. Railway automatically creates the database and sets `DATABASE_URL`

### Step 4: Configure Environment Variables

1. Click on your **bot service** (not the database)
2. Go to **"Variables"** tab
3. Click **"+ New Variable"**
4. Add:

```
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
```

**Important:** The `DATABASE_URL` is automatically set when you add PostgreSQL - don't add it manually!

### Step 5: Verify Deployment

1. Go to **"Deployments"** tab
2. Watch the build logs
3. Wait for status to show **"SUCCESS"** ✅
4. Check **"Logs"** to see your bot starting up

You should see:
```
Bot started successfully!
Database connected.
Polling for updates...
```

## Environment Variables Required

- `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
- `DATABASE_URL`: Automatically provided by Railway Postgres

## Configuration Files

### railway.toml
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python anonymous_chat_bot.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[[services]]
name = "telegram-bot"
source = "."

[services.variables]
TELEGRAM_BOT_TOKEN = { $ref = "TELEGRAM_BOT_TOKEN" }
DATABASE_URL = { $ref = "DATABASE_URL" }
```

### .python-version (NEW - Required!)
```
3.11
```

### nixpacks.toml (NEW - Ensures proper PostgreSQL support)
```toml
[phases.setup]
nixPkgs = ["postgresql"]

[start]
cmd = "python anonymous_chat_bot.py"
```

### railway.toml (FIXED)
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python anonymous_chat_bot.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### requirements.txt (FIXED - No duplicates)
```
python-telegram-bot[job-queue]==20.7
psycopg2-binary==2.9.10
python-dotenv==1.1.1
sqlalchemy==2.0.43
```

### runtime.txt
```
python-3.11.9
```

### Procfile (for compatibility)
```
worker: python anonymous_chat_bot.py
```

## Monitoring

### Check Logs
1. Go to Railway dashboard
2. Select your project
3. Click on "Deployments" tab
4. View real-time logs

### Check Service Status
- Railway dashboard shows service status
- Green = running, Red = stopped/error

### Database Access
1. Railway dashboard → PostgreSQL service
2. Use "Connect" tab for connection details
3. Can use railway CLI: `railway connect postgres`

## Bot Commands for Admin (ID: 1395596220)

- `/admin` - Access admin panel
- `/start` - Start bot and register
- `/help` - Show help menu

## Features

- Anonymous chat matching with retry system
- PostgreSQL database persistence  
- Admin control panel
- User reporting and moderation
- Broadcast messaging system
- Privacy protection features
- Automatic session management

## Railway CLI Commands

### Install Railway CLI
```bash
npm install -g @railway/cli
```

### Login and Deploy
```bash
railway login
railway link [project-id]
railway up
```

### Environment Variables
```bash
railway variables set TELEGRAM_BOT_TOKEN=your_token
railway variables list
```

### Logs
```bash
railway logs --follow
```

### Connect to Database
```bash
railway connect postgres
```

## Scaling

Railway automatically scales based on usage. For high-traffic bots:
1. Upgrade to Pro plan
2. Increase memory limits if needed
3. Consider multiple worker instances

## 🔧 Troubleshooting Common Errors

### ❌ Error: "ModuleNotFoundError: No module named 'telegram'"

**Cause:** Duplicate or conflicting packages in `requirements.txt`

**Solution:** ✅ Already fixed! The new `requirements.txt` removes:
- Duplicate entries
- Conflicting `telegram` package (conflicts with `python-telegram-bot`)

### ❌ Error: "Application failed to respond"

**Cause:** Bot not binding to correct port (only for web apps)

**Solution:** 
- Telegram bots don't need to bind to a port
- This is normal and can be ignored
- Railway might show this warning but bot will work

### ❌ Error: "psycopg2.OperationalError: could not connect to server"

**Cause:** PostgreSQL database not added or `DATABASE_URL` not set

**Solution:**
1. Make sure you added PostgreSQL service in Step 3
2. Check that both services are running
3. Verify `DATABASE_URL` exists in Variables tab
4. Restart the deployment

### ❌ Error: "python: can't open file 'anonymous_chat_bot.py'"

**Cause:** Wrong file path or missing file

**Solution:**
1. Verify file exists in your repository root
2. Check file name spelling (case-sensitive)
3. Make sure you pushed all files to GitHub

### ❌ Build Fails: "No Python version specified"

**Cause:** Missing Python version configuration

**Solution:** ✅ Already fixed! Added `.python-version` file

### ❌ Error: "telegram.error.InvalidToken"

**Cause:** Wrong or missing Telegram bot token

**Solution:**
1. Get your token from [@BotFather](https://t.me/BotFather)
2. Go to Railway → Your Service → Variables
3. Update `TELEGRAM_BOT_TOKEN` with correct token
4. Redeploy

### ❌ Bot starts but doesn't respond

**Cause:** Bot token might be used by another instance

**Solution:**
1. Stop any local instances of your bot
2. Check if bot is running elsewhere
3. Restart Railway deployment
4. Test with `/start` command in Telegram

### Memory Issues
1. Monitor resource usage in Railway dashboard
2. Railway free tier: 512MB RAM, 1GB disk
3. Upgrade plan if needed for high traffic

## Security

- Environment variables are encrypted
- Database access is secured by Railway
- No sensitive data stored in code
- Regular security updates via Railway platform

## Backup

Railway provides automatic database backups:
1. Go to PostgreSQL service in dashboard
2. "Backups" tab shows available backups
3. Can restore from any backup point

## Support

- Railway documentation: https://docs.railway.app
- Community Discord: https://discord.gg/railway
- Telegram Bot API docs: https://core.telegram.org/bots/api