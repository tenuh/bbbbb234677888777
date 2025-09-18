# Heroku Deployment Guide

## Quick Deploy

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Manual Deployment

### Prerequisites
1. Heroku account
2. Heroku CLI installed
3. Telegram Bot Token from @BotFather

### Step 1: Create Heroku App
```bash
heroku create your-bot-name
```

### Step 2: Add PostgreSQL Database
```bash
heroku addons:create heroku-postgresql:essential-0
```

### Step 3: Set Environment Variables
```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### Step 4: Deploy
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Step 5: Scale Worker Dyno
```bash
heroku ps:scale worker=1
```

## Environment Variables Required

- `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
- `DATABASE_URL`: Automatically provided by Heroku Postgres

## Monitoring

### Check logs
```bash
heroku logs --tail
```

### Check dyno status
```bash
heroku ps
```

### Access database
```bash
heroku pg:psql
```

## Bot Commands for Admin (ID: 1395596220)

- `/admin` - Access admin panel
- `/start` - Start bot and register
- `/help` - Show help menu

## Features

- Anonymous chat matching
- Database persistence
- Admin controls
- User reporting system
- Broadcast messaging
- Privacy protection
- Automatic retry matching

## Scaling

For high usage, upgrade dynos:
```bash
heroku ps:scale worker=1:standard-1x
heroku addons:upgrade heroku-postgresql:standard-0
```