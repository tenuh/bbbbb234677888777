# 🚀 Vercel Deployment - Quick Start

## 📝 Prerequisites Checklist

- [ ] Vercel account ([vercel.com](https://vercel.com))
- [ ] PostgreSQL database (Neon/Supabase/Railway)
- [ ] Telegram Bot Token (from @BotFather)

---

## ⚡ 5-Minute Deploy

### 1. Install Vercel CLI
```bash
npm install -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy Your Bot
```bash
vercel
```

### 4. Set Environment Variables
```bash
vercel env add TELEGRAM_BOT_TOKEN
# Enter your bot token when prompted

vercel env add DATABASE_URL  
# Enter your PostgreSQL URL when prompted
```

### 5. Deploy to Production
```bash
vercel --prod
```

### 6. Set Webhook URL
After deployment, you'll get a URL like `https://your-app.vercel.app`

Run the webhook setup script:
```bash
python set_webhook.py
```

Or manually visit:
```
https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://your-app.vercel.app/api/webhook
```

---

## ✅ Verify It Works

1. **Check webhook status:**
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
   ```

2. **Test your bot:**
   - Open Telegram
   - Find your bot
   - Send `/start`

---

## 📁 Files Created

- `vercel.json` - Vercel configuration
- `api/webhook.py` - Webhook handler
- `set_webhook.py` - Webhook setup script
- `VERCEL_DEPLOYMENT.md` - Full documentation

---

## 🐛 Quick Troubleshooting

**Bot not responding?**
- Check environment variables in Vercel Dashboard
- Verify webhook is set correctly
- Check Vercel function logs

**Database connection errors?**
- Verify DATABASE_URL format
- Add `?sslmode=require` to connection string
- Check database is publicly accessible

---

## 📚 Full Guide

For detailed instructions, see [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)

---

**That's it! Your bot is live on Vercel! 🎉**
