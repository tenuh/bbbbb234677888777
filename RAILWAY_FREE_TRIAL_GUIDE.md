# 🚂 Railway $5 Trial Deployment Guide (Step-by-Step)

## ⚠️ Important: Railway Pricing

**Railway NO LONGER has a free forever plan.**

- **Trial:** $5 credit (30 days) - **NO CREDIT CARD NEEDED**
- **After Trial:** $5/month Hobby plan required to keep bot running

**For truly FREE hosting forever, see `RENDER_FREE_DEPLOYMENT.md` instead!**

---

## 📋 What You Get with Trial

- ✅ **$5 credit** (one-time, lasts 30 days)
- ✅ **No credit card required** for trial
- ✅ Deploy databases + code
- ✅ 512MB RAM, shared CPU
- ❌ **Services stop** after 30 days or when credit runs out

---

## 🚀 Step-by-Step Deployment

### STEP 1: Create Railway Account (No Credit Card!)

1. Go to **https://railway.app**
2. Click **"Login"** (top right)
3. Click **"Login with GitHub"**
4. Authorize Railway to access your GitHub account
5. Complete signup - you'll get **$5 credit automatically** ✅

**Important:** Connect GitHub to get **Full Trial** (can deploy code + databases)

---

### STEP 2: Push Your Code to GitHub

If you haven't already:

```bash
# Initialize git (if needed)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Railway deployment"

# Create GitHub repo and push
# (Create repo on github.com first)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

### STEP 3: Create New Project on Railway

1. **Log into Railway** (https://railway.app/dashboard)
2. Click **"New Project"** button (big purple button)
3. Select **"Deploy from GitHub repo"**
4. If prompted, authorize Railway to access your repositories
5. **Select your bot repository** from the list
6. Railway will start building immediately!

---

### STEP 4: Add PostgreSQL Database

1. In your project dashboard, click **"+ New"** button
2. Select **"Database"**
3. Choose **"Add PostgreSQL"**
4. Wait for database to provision (~30 seconds)
5. Railway automatically creates `DATABASE_URL` variable ✅

---

### STEP 5: Configure Bot Token

1. Click on your **bot service** (NOT the database)
2. Go to **"Variables"** tab
3. Click **"+ New Variable"** button
4. Add:
   - **Variable name:** `TELEGRAM_BOT_TOKEN`
   - **Value:** Your token from @BotFather (looks like `7123456789:AAHdqTcv...`)
5. Click **"Add"**

**Important:** DON'T manually add `DATABASE_URL` - Railway sets this automatically!

---

### STEP 6: Wait for Deployment

1. Click on **"Deployments"** tab
2. Watch the build process:
   - **Cloning repository** ⏳
   - **Installing dependencies** ⏳
   - **Building** ⏳
   - **Starting** ⏳
3. Wait for status to show **"SUCCESS"** ✅ (usually 2-3 minutes)

---

### STEP 7: Check Logs

1. Go to **"Logs"** tab (or **"Deployments"** → click latest deployment)
2. You should see:
   ```
   Bot started successfully!
   Database connected.
   Polling for updates...
   ```

3. If you see this, **YOUR BOT IS LIVE!** 🎉

---

### STEP 8: Test Your Bot

1. Open Telegram
2. Search for your bot
3. Send **/start** command
4. Bot should respond immediately!

---

## 📊 Monitor Your Credit Usage

### Check Remaining Credit

1. Railway Dashboard → **"Usage"** tab
2. See how much of your $5 credit is left
3. Estimated date when credit runs out

**Typical usage for Telegram bot:**
- Small bot (few users): ~$0.10-0.50/day = ~$3-15/month
- Your $5 credit = ~10-30 days depending on traffic

---

## 🔧 Manage Your Bot

### View Real-Time Logs
1. Dashboard → Your bot service
2. Click **"Logs"** tab
3. See all messages in real-time

### Restart Bot
1. Dashboard → Your bot service
2. Go to **"Settings"** tab
3. Scroll down → Click **"Restart"**

### Update Bot Code
1. Make changes to your code locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update bot"
   git push
   ```
3. Railway **auto-deploys** within 1-2 minutes!

### Stop Bot (Save Credits)
1. Dashboard → Your bot service
2. Settings → Scroll to bottom
3. Click **"Delete Service"** (you can re-add later)

---

## ⚠️ What Happens After 30 Days?

### When Trial Ends:
1. **Your bot stops running** ❌
2. **Database data is kept** for 30 more days
3. You get email notification from Railway

### To Keep Bot Running:
1. Go to Railway Dashboard
2. Click **"Subscribe to Hobby Plan"**
3. **Add credit card** (required for paid plans)
4. Pay **$5/month** subscription
5. Get **$5 usage credit/month** included
6. Bot continues running ✅

**Cost:** ~$5-10/month depending on usage

---

## 🆓 Want Truly FREE Hosting?

Railway requires payment after trial. For **FREE FOREVER** hosting:

### Option 1: Render.com (Recommended)
- ✅ **FREE tier** (not a trial!)
- ✅ 512MB RAM, shared CPU
- ✅ PostgreSQL database included
- ✅ Auto-deploys from GitHub
- ❌ App sleeps after 15 min inactivity (restarts on new message)

**See:** `RENDER_FREE_DEPLOYMENT.md`

### Option 2: Oracle Cloud
- ✅ **FREE forever** 
- ✅ 4 CPUs + 24GB RAM
- ✅ PostgreSQL database
- ✅ True 24/7 uptime
- ❌ More complex setup

**See:** `ORACLE_CLOUD_DEPLOYMENT.md`

---

## 🔥 Troubleshooting

### ❌ Build Fails
**Check logs in Deployments tab:**
- Missing dependencies? Check `requirements.txt`
- Python version issue? `.python-version` should be `3.11`
- Check error messages and fix accordingly

### ❌ Bot Not Responding
1. Check **Logs** tab for errors
2. Verify `TELEGRAM_BOT_TOKEN` is correct
3. Make sure database is running (should show green status)
4. Check if another instance of bot is running elsewhere

### ❌ "Cannot deploy code" Error
- You need **Full Trial** (requires verified GitHub account)
- Connect GitHub account in Railway settings
- GitHub account must have activity (not brand new)

### ❌ Database Connection Error
1. Make sure PostgreSQL service is running
2. Check both services are in same project
3. `DATABASE_URL` should be set automatically
4. Restart bot service

### ❌ Out of Credit
- Check Usage tab
- Either upgrade to Hobby plan or use free alternatives

---

## 💡 Tips to Save Credits

1. **Stop bot when testing** - Only run when actually using
2. **Use free alternatives** for development/testing
3. **Monitor usage daily** in Railway dashboard
4. **Delete unused services** (databases you're not using)

---

## 📚 Important Files in Your Project

These files make Railway deployment work:

- ✅ `requirements.txt` - Python dependencies
- ✅ `.python-version` - Python 3.11
- ✅ `railway.toml` - Railway configuration
- ✅ `nixpacks.toml` - Build configuration
- ✅ `Procfile` - Backup start command

All files are already configured! ✅

---

## 🎉 Summary

| Step | What to Do |
|------|------------|
| 1 | Sign up on Railway with GitHub (get $5 credit) |
| 2 | Push code to GitHub |
| 3 | Create Railway project from your repo |
| 4 | Add PostgreSQL database |
| 5 | Set `TELEGRAM_BOT_TOKEN` variable |
| 6 | Wait for deployment (2-3 min) |
| 7 | Check logs for "Bot started" message |
| 8 | Test bot on Telegram with /start |

**Your bot runs for ~30 days on the $5 trial!**

After that, upgrade to Hobby plan ($5/month) or use free alternatives.

---

## 🔗 Useful Links

- **Railway Dashboard:** https://railway.app/dashboard
- **Railway Docs:** https://docs.railway.com
- **Railway Pricing:** https://railway.com/pricing
- **Get Bot Token:** https://t.me/BotFather

---

**Need truly free hosting? Check `RENDER_FREE_DEPLOYMENT.md` for Render.com guide!**
