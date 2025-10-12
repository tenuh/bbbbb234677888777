# 🚀 Vercel Deployment Guide for Telegram Bot

## ⚠️ Important Notice

**Vercel uses serverless functions** which work differently from traditional servers. This guide will help you deploy using **webhook mode** instead of polling.

### Why Webhook Mode?
- ✅ Works with Vercel's serverless architecture
- ✅ More efficient (Telegram sends updates to you)
- ✅ No constant polling needed
- ❌ Requires HTTPS URL (Vercel provides this automatically)

---

## 📋 Prerequisites

Before deploying to Vercel, you need:

1. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
2. **Telegram Bot Token** - Get from [@BotFather](https://t.me/BotFather)
3. **PostgreSQL Database** - Use one of these:
   - [Neon](https://neon.tech) (Recommended - Free tier)
   - [Supabase](https://supabase.com) (Free tier with PostgreSQL)
   - [Railway](https://railway.app) (PostgreSQL only)

---

## 🗄️ Step 1: Set Up Database

### Option A: Neon (Recommended)

1. Go to [neon.tech](https://neon.tech) and sign up
2. Create a new project
3. Copy the connection string (looks like):
   ```
   postgresql://username:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
   ```

### Option B: Supabase

1. Go to [supabase.com](https://supabase.com) and create account
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string (URI mode)

---

## 📁 Step 2: Prepare Your Project

### Create Vercel Configuration

Create a file called `vercel.json` in your project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/webhook.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/webhook",
      "dest": "api/webhook.py"
    }
  ],
  "env": {
    "TELEGRAM_BOT_TOKEN": "@telegram_bot_token",
    "DATABASE_URL": "@database_url"
  }
}
```

### Create API Directory Structure

```bash
mkdir -p api
```

---

## 🔧 Step 3: Create Webhook Handler

You need to create a webhook version of your bot. Here's how:

### Create `api/webhook.py`:

```python
from http.server import BaseHTTPRequestHandler
import json
import os
from telegram import Update
from telegram.ext import Application, ContextTypes
import asyncio

# Import your bot handlers (you'll need to refactor the main file)
from bot_handlers import setup_handlers

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# Create application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
setup_handlers(application)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Get the request body
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        # Parse update
        update_data = json.loads(body.decode('utf-8'))
        update = Update.de_json(update_data, application.bot)
        
        # Process update
        asyncio.run(application.process_update(update))
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())
        
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running!")
```

---

## 🚀 Step 4: Deploy to Vercel

### Method 1: Using Vercel CLI (Recommended)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   vercel
   ```

4. **Follow the prompts:**
   - Set up and deploy? **Yes**
   - Which scope? **Your account**
   - Link to existing project? **No**
   - Project name? **telegram-bot** (or your choice)
   - Directory? **./  (current directory)**
   - Override settings? **No**

5. **Set Environment Variables**
   ```bash
   vercel env add TELEGRAM_BOT_TOKEN
   vercel env add DATABASE_URL
   ```
   
   Enter the values when prompted.

6. **Deploy to Production**
   ```bash
   vercel --prod
   ```

### Method 2: Using Vercel Dashboard

1. **Go to [vercel.com/new](https://vercel.com/new)**

2. **Import Git Repository**
   - Connect your GitHub/GitLab/Bitbucket
   - Select your repository
   - Click Import

3. **Configure Project**
   - Framework Preset: **Other**
   - Root Directory: **./  (leave blank)**
   - Build Command: **leave blank**
   - Output Directory: **leave blank**

4. **Add Environment Variables**
   - Click "Environment Variables"
   - Add:
     - `TELEGRAM_BOT_TOKEN` = your bot token
     - `DATABASE_URL` = your database connection string

5. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete

---

## 🔗 Step 5: Set Webhook URL

After deployment, you'll get a URL like: `https://your-app.vercel.app`

### Set the webhook:

**Option 1: Using Browser**

Visit this URL in your browser (replace with your values):
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app.vercel.app/api/webhook
```

**Option 2: Using curl**
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app.vercel.app/api/webhook"}'
```

**Option 3: Using Python Script**

Create `set_webhook.py`:
```python
import requests
import os

BOT_TOKEN = "your_bot_token_here"
WEBHOOK_URL = "https://your-app.vercel.app/api/webhook"

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={"url": WEBHOOK_URL}
)

print(response.json())
```

Run it:
```bash
python set_webhook.py
```

---

## ✅ Step 6: Verify Deployment

1. **Check Webhook Status**
   Visit:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
   ```

2. **Test Your Bot**
   - Open Telegram
   - Find your bot
   - Send `/start`
   - The bot should respond!

3. **Check Logs**
   - Go to Vercel Dashboard
   - Click on your project
   - Go to "Functions" tab
   - Check logs for any errors

---

## 🐛 Troubleshooting

### Bot Not Responding

**Check Webhook Status:**
```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

**Common Issues:**

1. **Webhook URL is wrong**
   - Make sure it ends with `/api/webhook`
   - Must be HTTPS (Vercel provides this)

2. **Environment variables not set**
   - Check Vercel Dashboard → Settings → Environment Variables
   - Redeploy after adding variables

3. **Database connection failed**
   - Verify DATABASE_URL is correct
   - Check database is accessible from Vercel

### Function Timeout

Vercel has execution time limits:
- **Hobby**: 10 seconds
- **Pro**: 60 seconds

If functions timeout:
- Optimize database queries
- Use connection pooling
- Upgrade to Pro plan

### Database Connection Issues

Add to your `DATABASE_URL`:
```
?sslmode=require&connect_timeout=10
```

---

## 📊 Vercel Dashboard Features

### View Logs
1. Go to your project
2. Click "Deployments"
3. Click on latest deployment
4. Go to "Functions" tab
5. Click on a function to see logs

### Environment Variables
1. Go to Settings
2. Click "Environment Variables"
3. Add/Edit/Delete variables
4. Redeploy for changes to take effect

### Custom Domain
1. Go to Settings
2. Click "Domains"
3. Add your custom domain
4. Follow DNS configuration steps

---

## 🔄 Updating Your Bot

### Using Git (Automatic Deployment)

1. Make changes to your code
2. Commit and push:
   ```bash
   git add .
   git commit -m "Update bot"
   git push
   ```
3. Vercel automatically deploys!

### Using Vercel CLI

```bash
vercel --prod
```

---

## 💰 Pricing

### Vercel Pricing
- **Hobby** (Free):
  - 100GB bandwidth/month
  - 100 hours function execution
  - 10s function timeout
  
- **Pro** ($20/month):
  - 1TB bandwidth
  - 1000 hours execution
  - 60s function timeout

### Database Pricing
- **Neon** (Free): 500MB storage, 1 project
- **Supabase** (Free): 500MB database, 2GB bandwidth

---

## ⚡ Performance Tips

1. **Use Connection Pooling**
   ```python
   from sqlalchemy.pool import NullPool
   engine = create_engine(DATABASE_URL, poolclass=NullPool)
   ```

2. **Optimize Database Queries**
   - Use indexes
   - Limit query results
   - Use selective loading

3. **Cache Frequently Used Data**
   - Use Vercel KV (key-value store)
   - Cache user profiles

4. **Minimize Cold Starts**
   - Keep functions small
   - Use lazy imports
   - Optimize dependencies

---

## 🔐 Security Best Practices

1. **Never commit secrets**
   - Use Vercel environment variables
   - Add `.env` to `.gitignore`

2. **Verify webhook requests**
   ```python
   # Add secret token validation
   SECRET_TOKEN = os.getenv('SECRET_TOKEN')
   ```

3. **Use HTTPS only**
   - Vercel provides automatic HTTPS
   - Never use HTTP for webhooks

4. **Validate user input**
   - Sanitize all inputs
   - Check for SQL injection
   - Validate file uploads

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [python-telegram-bot Webhooks](https://docs.python-telegram-bot.org/en/stable/telegram.ext.updater.html)
- [Neon Documentation](https://neon.tech/docs)

---

## 🎉 You're Done!

Your Telegram bot is now deployed on Vercel! 🚀

**Next Steps:**
- Customize your bot features
- Monitor usage in Vercel Dashboard
- Set up custom domain (optional)
- Upgrade plan if needed

Need help? Check the [Troubleshooting](#-troubleshooting) section or contact support.

---

## 📝 Quick Command Reference

```bash
# Deploy to Vercel
vercel

# Deploy to production
vercel --prod

# Set environment variable
vercel env add VARIABLE_NAME

# View logs
vercel logs

# Remove deployment
vercel rm project-name
```

---

## ⚠️ Important Notes

1. **This bot uses webhook mode** - Different from polling mode
2. **Vercel has function timeouts** - Optimize long-running tasks
3. **Database must be accessible** - Use cloud databases (Neon, Supabase)
4. **HTTPS is required** - Telegram webhooks need HTTPS (Vercel provides this)

---

**Happy Deploying! 🎊**
