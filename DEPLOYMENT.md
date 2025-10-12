# 🚀 Deployment Guide

This guide covers deploying your Telegram Anonymous Chat Bot to various platforms.

## 📋 Table of Contents
- [Replit Deployment (Recommended)](#replit-deployment)
- [Railway Deployment](#railway-deployment)
- [Heroku Deployment](#heroku-deployment)
- [Vercel Deployment (Webhook Mode)](#vercel-deployment)
- [Environment Variables](#environment-variables)

---

## 🔵 Replit Deployment (Recommended)

Replit provides the easiest deployment with built-in PostgreSQL database.

### Steps:
1. **Setup Database**
   - Click "Database" in the sidebar
   - Create a new PostgreSQL database
   - The `DATABASE_URL` is automatically set

2. **Add Bot Token**
   - Go to "Secrets" (🔒 icon)
   - Add secret: `TELEGRAM_BOT_TOKEN` = your bot token from @BotFather

3. **Deploy**
   - Click the "Deploy" button
   - Choose "Autoscale" or "Reserved VM"
   - Your bot will be live!

### Features:
- ✅ Built-in PostgreSQL database
- ✅ Automatic SSL/HTTPS
- ✅ Easy environment management
- ✅ One-click deployment

---

## 🚂 Railway Deployment

Railway offers excellent support for Python apps with PostgreSQL.

### Steps:
1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Create New Project**
   ```bash
   railway init
   ```

3. **Add PostgreSQL**
   ```bash
   railway add postgresql
   ```

4. **Set Environment Variables**
   ```bash
   railway variables set TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

5. **Deploy**
   ```bash
   railway up
   ```

### Configuration:
The `railway.toml` file is already configured:
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python anonymous_chat_bot.py"
restartPolicyType = "on_failure"
```

---

## 🟣 Heroku Deployment

### Prerequisites:
- Heroku account
- Heroku CLI installed

### Steps:
1. **Login to Heroku**
   ```bash
   heroku login
   ```

2. **Create App**
   ```bash
   heroku create your-app-name
   ```

3. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

### Configuration Files:
- `Procfile`: Defines how to run the app
- `runtime.txt`: Specifies Python version
- `requirements.txt`: Lists dependencies

---

## ▲ Vercel Deployment (Webhook Mode)

**Note:** Vercel is designed for serverless functions. For Telegram bots, you'll need to use webhook mode instead of polling.

### ⚠️ Important:
This requires modifying the bot to use webhooks instead of polling. The current bot uses polling mode and is **not compatible** with Vercel's serverless architecture.

### Alternative: Use Vercel for Frontend + Railway/Heroku for Bot
- Deploy a web dashboard on Vercel
- Deploy the bot on Railway/Heroku
- This gives you the best of both worlds

### Why Vercel Isn't Ideal for This Bot:
- ❌ No support for long-running processes
- ❌ Requires webhook setup (complex)
- ❌ Function timeout limits (10-60 seconds)
- ❌ Additional complexity in state management

### Recommended Approach:
Use **Railway** or **Replit** for this Telegram bot instead.

---

## 🔐 Environment Variables

All platforms require these environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | ✅ Yes |
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes |

### Getting Your Bot Token:
1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the token provided

### Database URL Format:
```
postgresql://user:password@host:port/database
```

Most platforms (Replit, Railway, Heroku) provide this automatically when you add PostgreSQL.

---

## 🎯 Quick Deployment Comparison

| Platform | Difficulty | Cost | Database | Best For |
|----------|-----------|------|----------|----------|
| **Replit** | ⭐ Easy | Free tier available | ✅ Built-in | Beginners, prototypes |
| **Railway** | ⭐⭐ Medium | $5/month after trial | ✅ Easy setup | Production apps |
| **Heroku** | ⭐⭐ Medium | $7/month (Eco) | ✅ Add-on available | Established apps |
| **Vercel** | ⭐⭐⭐⭐ Hard | Free tier | ❌ External needed | **Not Recommended** |

---

## 🚀 Post-Deployment

After deploying:

1. **Test Your Bot**
   - Open Telegram
   - Search for your bot
   - Send `/start`

2. **Monitor Logs**
   - Check platform dashboard for errors
   - Ensure database connection works

3. **Set Bot Commands** (Optional)
   - The bot automatically sets commands on startup
   - Or manually via @BotFather

---

## 🐛 Troubleshooting

### Bot Not Responding:
- ✅ Check if the bot is running in platform dashboard
- ✅ Verify `TELEGRAM_BOT_TOKEN` is correct
- ✅ Check logs for errors

### Database Errors:
- ✅ Ensure `DATABASE_URL` is set correctly
- ✅ Check database is running
- ✅ Verify connection string format

### Common Issues:
```bash
# Error: "Database not found"
Solution: Create PostgreSQL database on your platform

# Error: "Invalid bot token"
Solution: Get new token from @BotFather

# Error: "Port already in use"
Solution: This bot doesn't use ports, check configuration
```

---

## 📚 Additional Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [Railway Documentation](https://docs.railway.app/)
- [Heroku Python Support](https://devcenter.heroku.com/categories/python-support)

---

## 💡 Tips

1. **Always use environment variables** for sensitive data
2. **Enable auto-deploy** from your git repository
3. **Monitor usage** to stay within free tier limits
4. **Backup your database** regularly
5. **Test locally first** before deploying

---

## 🎉 You're All Set!

Your anonymous chat bot should now be running! Users can start chatting by finding your bot on Telegram and sending `/start`.

Happy chatting! 🎭
