# 🎨 Render.com FREE Deployment Guide (Forever Free!)

## ✅ Why Render.com?

- ✅ **100% FREE forever** (not a trial!)
- ✅ **No credit card required**
- ✅ PostgreSQL database included
- ✅ Auto-deploys from GitHub
- ✅ Easy setup (5 minutes)
- ⚠️ **App sleeps after 15 min inactivity** (wakes up automatically on new message)

**Perfect for Telegram bots with moderate traffic!**

---

## 🚀 Step-by-Step Deployment

### STEP 1: Create Render Account (FREE)

1. Go to **https://render.com**
2. Click **"Get Started"** or **"Sign Up"**
3. Choose **"Sign up with GitHub"**
4. Authorize Render to access your GitHub
5. Complete registration - **No credit card needed!** ✅

---

### STEP 2: Push Code to GitHub

Make sure your code is on GitHub:

```bash
# If not already done
git init
git add .
git commit -m "Prepare for Render deployment"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

### STEP 3: Create PostgreSQL Database

1. **Log into Render Dashboard** (https://dashboard.render.com)
2. Click **"New +"** button (top right)
3. Select **"PostgreSQL"**
4. Fill in database details:
   - **Name:** `telegram-bot-db`
   - **Database:** `telegram_bot` (auto-filled)
   - **User:** `telegram_bot` (auto-filled)
   - **Region:** Choose closest to you (e.g., Oregon USA, Frankfurt)
   - **PostgreSQL Version:** 16 (latest)
   - **Plan:** Select **"Free"** ✅
5. Click **"Create Database"**
6. Wait 1-2 minutes for database to provision

---

### STEP 4: Get Database Connection String

1. Click on your database name in dashboard
2. Scroll to **"Connections"** section
3. Copy the **"Internal Database URL"** 
   - Looks like: `postgres://user:password@...render.com/dbname`
4. **Save this** - you'll need it in Step 6!

---

### STEP 5: Create Web Service for Your Bot

1. Click **"New +"** again
2. Select **"Web Service"**
3. Click **"Build and deploy from a Git repository"** → **"Next"**
4. **Connect your GitHub repository:**
   - If first time: Click **"Connect account"** → Authorize Render
   - Select your bot repository from list
   - Click **"Connect"**

---

### STEP 6: Configure Web Service

Fill in these settings:

**Basic Settings:**
- **Name:** `telegram-bot` (or your preferred name)
- **Region:** Same as database (e.g., Oregon)
- **Branch:** `main`
- **Root Directory:** Leave blank
- **Runtime:** Select **"Python 3"** (should auto-detect)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python anonymous_chat_bot.py`

**Instance Type:**
- Select **"Free"** ✅ ($0/month)

---

### STEP 7: Add Environment Variables

Scroll down to **"Environment Variables"** section:

1. Click **"Add Environment Variable"**

2. **First variable:**
   - **Key:** `TELEGRAM_BOT_TOKEN`
   - **Value:** Your bot token from @BotFather
   - Click **"Save"**

3. Click **"Add Environment Variable"** again

4. **Second variable:**
   - **Key:** `DATABASE_URL`
   - **Value:** Paste the Internal Database URL from Step 4
   - Click **"Save"**

5. Click **"Add Environment Variable"** one more time

6. **Third variable:**
   - **Key:** `PYTHON_VERSION`
   - **Value:** `3.11.9`
   - Click **"Save"**

---

### STEP 8: Deploy!

1. Scroll to bottom
2. Click **"Create Web Service"** button
3. Render will start building your bot:
   - Cloning repository ⏳
   - Installing dependencies ⏳
   - Starting bot ⏳
4. Wait 3-5 minutes for first deployment

---

### STEP 9: Check Deployment Logs

1. You'll be on your service dashboard
2. Click **"Logs"** tab (left sidebar)
3. Watch for:
   ```
   Bot started successfully!
   Database connected.
   Polling for updates...
   ```
4. When you see this, **YOUR BOT IS LIVE!** 🎉

---

### STEP 10: Test Your Bot

1. Open Telegram
2. Find your bot
3. Send **/start**
4. Bot should respond immediately!

---

## ⚠️ Important: Free Tier Limitations

### Sleep After Inactivity
- **Free tier apps sleep after 15 minutes** of no incoming requests
- Bot will **wake up automatically** when someone messages it
- First message after sleep takes **~30-60 seconds** to wake up
- After waking, bot responds instantly

### How This Affects Your Bot:
- ✅ **Works fine** for low-to-medium traffic bots
- ✅ **Always free**, never expires
- ⚠️ First message after sleep is slower
- ⚠️ Not ideal for bots that need instant responses 24/7

**For true 24/7 instant responses, use Oracle Cloud (see `ORACLE_CLOUD_DEPLOYMENT.md`)**

---

## 🔧 Manage Your Bot

### View Logs in Real-Time
1. Dashboard → Your service
2. Click **"Logs"** tab
3. See all bot activity live

### Restart Bot
1. Dashboard → Your service
2. Click **"Manual Deploy"** → **"Clear build cache & deploy"**

### Update Bot Code
1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update bot features"
   git push
   ```
3. Render **auto-deploys** within 2-3 minutes! ✅

### Change Environment Variables
1. Dashboard → Your service
2. Click **"Environment"** tab (left sidebar)
3. Edit variables
4. Service auto-redeploys

### Suspend Service (Stop Bot)
1. Dashboard → Your service
2. Click **"Settings"** tab
3. Scroll to "Suspend Web Service"
4. Click **"Suspend"**
5. Re-enable anytime by clicking **"Resume"**

---

## 📊 Monitor Your Bot

### Check Service Status
- Dashboard shows: **"Live"** (green) = Running
- **"Deploying"** (yellow) = Building/starting
- **"Suspended"** (gray) = Stopped

### View Database
1. Dashboard → Your PostgreSQL database
2. Click **"Info"** tab
3. See connection details, usage stats

### Free Tier Limits
- **750 hours/month** of service runtime (enough for 24/7!)
- **100 GB bandwidth/month**
- **256 MB RAM**
- **0.1 CPU**
- **PostgreSQL:** 256MB RAM, 1GB storage, 90 days data retention

---

## 🚀 Upgrade to Paid (Optional)

If you need 24/7 instant responses with no sleep:

### Render Paid Plans
- **Starter:** $7/month (no sleep, better resources)
- **Standard:** $25/month (more RAM/CPU)

### To Upgrade:
1. Dashboard → Your service
2. Settings → Change Instance Type
3. Select paid tier
4. Add payment method

**Or use Oracle Cloud free tier for better free 24/7 hosting!**

---

## 🔥 Troubleshooting

### ❌ Build Fails

**Check build logs:**
1. Dashboard → Your service → Logs
2. Look for error messages
3. Common issues:
   - Missing dependencies in `requirements.txt`
   - Wrong Python version
   - File path errors

**Solutions:**
- Verify all files committed to GitHub
- Check `.python-version` is `3.11`
- Make sure `requirements.txt` is in repo root

### ❌ Bot Not Responding

1. **Check if service is live:**
   - Dashboard should show green "Live" status
   
2. **Check logs for errors:**
   - Logs tab → Look for red error messages
   
3. **Verify bot token:**
   - Environment tab → Check `TELEGRAM_BOT_TOKEN` is correct
   
4. **Check database connection:**
   - Logs should show "Database connected"
   - Verify `DATABASE_URL` is set correctly

5. **Stop other instances:**
   - Only one instance can use a bot token at a time
   - Stop any local/other deployments

### ❌ "Application Failed to Respond"

This is normal for Telegram bots! They don't serve web traffic.

**Solution:** Ignore this error - bot still works via Telegram polling

### ❌ Service Keeps Sleeping

Free tier sleeps after inactivity - this is normal.

**Options:**
1. Accept the ~30s wake-up delay (still free!)
2. Upgrade to paid plan ($7/mo for no sleep)
3. Use Oracle Cloud free tier (true 24/7)

### ❌ Database Connection Errors

1. **Check database is running:**
   - Dashboard → PostgreSQL database
   - Should show "Available" status

2. **Verify DATABASE_URL:**
   - Environment tab
   - Should start with `postgres://`
   - Must be the "Internal" URL, not "External"

3. **Restart both services:**
   - Database → Info → Restart
   - Web Service → Manual Deploy

---

## 💡 Pro Tips

### Keep Bot Awake (Optional)

If you want to minimize sleep time, use an uptime monitor:

1. Sign up at https://uptimerobot.com (free)
2. Create new monitor:
   - Type: HTTP(s)
   - URL: Your Render service URL
   - Interval: 5 minutes
3. This pings your service regularly

**Note:** This won't completely prevent sleep on free tier, but reduces it.

### Better Alternative for 24/7

For **true 24/7** with instant responses, use:
- **Oracle Cloud** (free tier, 4 CPUs, 24GB RAM)
- See `ORACLE_CLOUD_DEPLOYMENT.md`

---

## 📋 Comparison: Render vs Others

| Feature | Render (Free) | Railway (Trial) | Oracle Cloud (Free) |
|---------|---------------|-----------------|---------------------|
| **Cost** | Free forever | $5 trial (30 days) | Free forever |
| **Credit Card** | Not required | Not required | Not required |
| **RAM** | 256 MB | 512 MB | 24 GB |
| **CPU** | 0.1 | Shared | 4 cores |
| **Database** | PostgreSQL ✅ | PostgreSQL ✅ | PostgreSQL ✅ |
| **Sleep** | After 15 min | No sleep | No sleep |
| **Auto-deploy** | GitHub ✅ | GitHub ✅ | Manual |
| **Setup Difficulty** | Easy ⭐⭐ | Easy ⭐⭐ | Medium ⭐⭐⭐⭐ |
| **Best For** | Low traffic bots | Testing (30 days) | Production 24/7 |

---

## 🎉 You're Done!

Your Telegram bot is now:
- ✅ Running on Render.com
- ✅ **100% FREE forever**
- ✅ Auto-deploying from GitHub
- ✅ Connected to PostgreSQL database
- ✅ Accessible to all Telegram users

**Limitations:**
- ⚠️ Sleeps after 15 min inactivity
- ⚠️ ~30s wake-up time on first message

**For 24/7 instant responses, upgrade to paid or use Oracle Cloud free tier!**

---

## 🔗 Useful Links

- **Render Dashboard:** https://dashboard.render.com
- **Render Docs:** https://render.com/docs
- **Render Free Tier:** https://render.com/docs/free
- **PostgreSQL Guide:** https://render.com/docs/databases
- **Get Bot Token:** https://t.me/BotFather

---

**Questions? Check the Troubleshooting section or Render's excellent documentation!**
