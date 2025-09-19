# Railway Deployment Guide

## Quick Deploy to Railway

### Prerequisites
1. Railway account (https://railway.app)
2. GitHub repository with your bot code
3. Telegram Bot Token from @BotFather

### Step 1: Create Railway Project
1. Go to https://railway.app and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### Step 2: Configure Environment Variables
In Railway dashboard, go to your project → Variables and add:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### Step 3: Add PostgreSQL Database
1. In Railway project dashboard, click "Add service"
2. Choose "PostgreSQL"
3. Railway will automatically create the database and set DATABASE_URL

### Step 4: Deploy
1. Railway will automatically deploy on git push
2. Your bot will start running immediately
3. Check logs in Railway dashboard

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

### runtime.txt
```
python-3.11.9
```

### requirements.txt
```
python-telegram-bot[job-queue]==20.7
psycopg2-binary==2.9.10
python-dotenv==1.1.1
sqlalchemy==2.0.43
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

## Troubleshooting

### Bot Not Responding
1. Check Railway logs for errors
2. Verify TELEGRAM_BOT_TOKEN is set correctly
3. Ensure database is connected

### Database Issues
1. Check DATABASE_URL variable
2. Verify PostgreSQL service is running
3. Check database logs in Railway dashboard

### Memory Issues
1. Monitor resource usage in Railway dashboard
2. Upgrade plan if needed
3. Optimize code for memory usage

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