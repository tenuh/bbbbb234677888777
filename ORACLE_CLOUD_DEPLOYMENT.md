# 🚀 Deploy Telegram Anonymous Chat Bot to Oracle Cloud Free Tier

## 🎯 What You'll Get (100% FREE Forever)

Oracle Cloud Always Free Tier provides:
- **4 ARM OCPUs + 24GB RAM** (Ampere A1) - Perfect for your bot!
- **200GB storage**
- **10TB monthly bandwidth**
- **24/7 uptime** - No time limits, truly free forever
- **PostgreSQL database** (can use Oracle Autonomous Database or install PostgreSQL)

---

## 📋 Prerequisites

Before starting, you need:
1. ✅ Telegram Bot Token from [@BotFather](https://t.me/BotFather)
2. ✅ Credit/debit card for Oracle account verification (won't be charged)
3. ✅ Your bot code (already in this project!)
4. ✅ Basic terminal knowledge

---

## STEP 1: Create Oracle Cloud Account

### 1.1 Sign Up
1. Go to **https://www.oracle.com/cloud/free/**
2. Click **"Start for free"**
3. Fill in your details:
   - Email, name, country/region
   - Choose your **home region** carefully (cannot change later)
   - Recommended regions: US East (Ashburn), US West (Phoenix), or EU (Frankfurt)
4. Add credit card for identity verification
   - You will **NOT be charged** on free tier
   - Only used to verify you're not a bot
5. Complete registration
6. Wait for confirmation email (usually instant, sometimes up to 48 hours)

### 1.2 Activate Account
1. Check your email for account activation
2. Set your password
3. Log in to **Oracle Cloud Console**

---

## STEP 2: Create Your Free VM Instance

### 2.1 Navigate to Compute
1. Log into **Oracle Cloud Console**
2. Click **☰** menu (top left)
3. Go to **Compute → Instances**
4. Click **"Create Instance"**

### 2.2 Configure Instance Settings

**Name your instance:**
```
telegram-bot-server
```

**Image & Shape:**

1. **Click "Edit" next to Image**
   - Select **"Canonical Ubuntu"** 
   - Choose **Ubuntu 22.04** (or latest)
   - Look for **"Always Free-eligible"** badge ✅
   - Click **"Select Image"**

2. **Click "Change Shape"**
   - Select **"Ampere"** (ARM-based processors)
   - Choose **VM.Standard.A1.Flex**
   - Set resources:
     - **OCPUs:** 4 (maximum free tier)
     - **Memory (GB):** 24 (maximum free tier)
   - Verify **"Always Free-eligible"** shows ✅
   - Click **"Select Shape"**

**Networking:**

1. Keep default **Virtual Cloud Network (VCN)**
2. Keep default **Subnet**
3. **Public IPv4 address:** ✅ Assign a public IPv4 address
4. Leave other settings as default

**SSH Keys:**

1. Select **"Generate a key pair for me"**
2. Click **"Save Private Key"** 
   - Save as `telegram-bot-key.key` (important!)
3. Click **"Save Public Key"** (optional backup)
4. **Store these keys safely** - you'll need them to access your server

### 2.3 Create Instance
1. Click **"Create"**
2. Wait 2-3 minutes while Oracle provisions your instance
3. Instance status will change to **"Running"** (green)
4. **Copy your Public IP address** - you'll need this!

---

## STEP 3: Configure Firewall (Security Lists)

### 3.1 Open Required Ports in Oracle Cloud

1. In your **Instance Details** page, scroll down
2. Under **"Primary VNIC"**, click your **Subnet** link
3. Click **"Default Security List for [your-vcn]"**
4. Click **"Add Ingress Rules"**

**Add HTTPS Rule (for webhooks):**
- **Source Type:** CIDR
- **Source CIDR:** `0.0.0.0/0`
- **IP Protocol:** TCP
- **Destination Port Range:** `443`
- **Description:** `Telegram webhook HTTPS`
- Click **"Add Ingress Rules"**

**Add HTTP Rule (optional, for health checks):**
- **Source CIDR:** `0.0.0.0/0`
- **IP Protocol:** TCP
- **Destination Port Range:** `80`
- **Description:** `HTTP traffic`
- Click **"Add Ingress Rules"**

---

## STEP 4: Connect to Your VM via SSH

### 4.1 Set Key Permissions (Linux/Mac)

Open terminal and run:
```bash
chmod 400 ~/Downloads/telegram-bot-key.key
```

### 4.2 Connect via SSH

```bash
ssh -i ~/Downloads/telegram-bot-key.key ubuntu@YOUR_PUBLIC_IP
```

Replace `YOUR_PUBLIC_IP` with your actual IP address from Step 2.3.

**For Windows users:**
- Use **Windows Terminal** with the same command above, or
- Use **PuTTY** and load your private key file

### 4.3 Accept Host Key
When prompted "Are you sure you want to continue connecting?", type **yes**

You're now connected to your Oracle Cloud VM! 🎉

---

## STEP 5: Install System Dependencies

### 5.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 5.2 Install Python & Essential Tools
```bash
sudo apt install python3 python3-pip python3-venv git postgresql postgresql-contrib -y
```

### 5.3 Verify Installation
```bash
python3 --version  # Should show Python 3.10+
pip3 --version
psql --version
```

---

## STEP 6: Set Up PostgreSQL Database

### 6.1 Start PostgreSQL Service
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 6.2 Create Database and User
```bash
# Switch to postgres user
sudo -i -u postgres

# Create database
createdb telegram_bot_db

# Create user and grant privileges
psql -c "CREATE USER botuser WITH PASSWORD 'YourStrongPassword123';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE telegram_bot_db TO botuser;"
psql -c "ALTER DATABASE telegram_bot_db OWNER TO botuser;"

# Exit postgres user
exit
```

### 6.3 Configure PostgreSQL for Local Access
```bash
# Test connection
psql -h localhost -U botuser -d telegram_bot_db -W
# Enter password: YourStrongPassword123
# Type \q to quit
```

---

## STEP 7: Upload Your Bot Code

### 7.1 Clone Your Repository (if using Git)
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git telegram-bot
cd telegram-bot
```

### 7.2 OR Upload Files Manually

If you don't have Git repository, create files manually:

```bash
# Create project directory
mkdir ~/telegram-bot
cd ~/telegram-bot

# You'll need to copy your files here
# Use scp from your local machine:
```

From your **local machine** (not SSH session):
```bash
scp -i ~/Downloads/telegram-bot-key.key anonymous_chat_bot.py ubuntu@YOUR_PUBLIC_IP:~/telegram-bot/
scp -i ~/Downloads/telegram-bot-key.key database.py ubuntu@YOUR_PUBLIC_IP:~/telegram-bot/
scp -i ~/Downloads/telegram-bot-key.key requirements.txt ubuntu@YOUR_PUBLIC_IP:~/telegram-bot/
```

---

## STEP 8: Install Python Dependencies

### 8.1 Create Virtual Environment
```bash
cd ~/telegram-bot
python3 -m venv venv
source venv/bin/activate
```

### 8.2 Install Requirements
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

You should see installations for:
- python-telegram-bot
- SQLAlchemy
- psycopg2-binary
- And other dependencies

---

## STEP 9: Configure Environment Variables

### 9.1 Create Environment File
```bash
nano ~/.env
```

### 9.2 Add Your Configuration
```bash
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# Database Connection
DATABASE_URL=postgresql://botuser:YourStrongPassword123@localhost/telegram_bot_db
```

**Important:** Replace:
- `your_bot_token_from_botfather` with your actual bot token
- `YourStrongPassword123` with the password you set in Step 6.2

Save file: `Ctrl+O`, then `Enter`, then `Ctrl+X`

### 9.3 Load Environment Variables
```bash
echo 'export $(cat ~/.env | xargs)' >> ~/.bashrc
source ~/.bashrc
```

---

## STEP 10: Open VM Firewall (Ubuntu Firewall)

Oracle Cloud has two firewalls - we configured one in Step 3. Now configure the Ubuntu firewall:

```bash
# Allow HTTP/HTTPS
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

# Install iptables-persistent to save rules
sudo apt install iptables-persistent -y

# Save current rules
sudo netfilter-persistent save
```

---

## STEP 11: Test Your Bot Manually

### 11.1 Run Bot
```bash
cd ~/telegram-bot
source venv/bin/activate
python3 anonymous_chat_bot.py
```

### 11.2 Test on Telegram
1. Open Telegram
2. Search for your bot
3. Send `/start` command
4. If it responds, **SUCCESS!** ✅

Press `Ctrl+C` to stop the bot.

---

## STEP 12: Make Bot Run 24/7 with systemd

### 12.1 Create systemd Service File
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

### 12.2 Paste Configuration
```ini
[Unit]
Description=Telegram Anonymous Chat Bot
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram-bot
Environment="TELEGRAM_BOT_TOKEN=your_bot_token_here"
Environment="DATABASE_URL=postgresql://botuser:YourStrongPassword123@localhost/telegram_bot_db"
ExecStart=/home/ubuntu/telegram-bot/venv/bin/python3 /home/ubuntu/telegram-bot/anonymous_chat_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**⚠️ Important:** Replace:
- `your_bot_token_here` with your actual Telegram bot token
- `YourStrongPassword123` with your database password

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### 12.3 Enable and Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable telegram-bot.service

# Start service now
sudo systemctl start telegram-bot.service

# Check status
sudo systemctl status telegram-bot.service
```

You should see:
```
● telegram-bot.service - Telegram Anonymous Chat Bot
   Loaded: loaded (/etc/systemd/system/telegram-bot.service; enabled)
   Active: active (running) since...
```

If you see **"active (running)"** in green, your bot is now running 24/7! 🎉

---

## STEP 13: Manage Your Bot

### 13.1 Useful Commands

**View real-time logs:**
```bash
sudo journalctl -u telegram-bot.service -f
```
Press `Ctrl+C` to exit

**View last 50 log lines:**
```bash
sudo journalctl -u telegram-bot.service -n 50
```

**Restart bot:**
```bash
sudo systemctl restart telegram-bot.service
```

**Stop bot:**
```bash
sudo systemctl stop telegram-bot.service
```

**Start bot:**
```bash
sudo systemctl start telegram-bot.service
```

**Check bot status:**
```bash
sudo systemctl status telegram-bot.service
```

### 13.2 Update Bot Code

When you need to update your bot:

```bash
cd ~/telegram-bot

# If using Git:
git pull

# If copying files manually, use scp as in Step 7.2

# Restart service
sudo systemctl restart telegram-bot.service
```

---

## STEP 14: Monitor System Resources

### 14.1 Check CPU/RAM Usage
```bash
htop
```
Press `q` to quit

### 14.2 Check Disk Space
```bash
df -h
```

### 14.3 Check Database Size
```bash
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('telegram_bot_db'));"
```

---

## 🎉 SUCCESS! Your Bot is Now Running 24/7

Your Telegram Anonymous Chat Bot is now:
- ✅ Running 24/7 on Oracle Cloud
- ✅ Using PostgreSQL database for persistence
- ✅ Auto-restarting on crashes
- ✅ Auto-starting on server reboots
- ✅ Completely FREE forever
- ✅ With 4 CPU cores and 24GB RAM

---

## 🔥 Troubleshooting

### Bot Won't Start?

**Check logs for errors:**
```bash
sudo journalctl -u telegram-bot.service -n 50 --no-pager
```

**Common issues:**

1. **Wrong bot token:**
   - Edit service file: `sudo nano /etc/systemd/system/telegram-bot.service`
   - Update `TELEGRAM_BOT_TOKEN`
   - Reload: `sudo systemctl daemon-reload`
   - Restart: `sudo systemctl restart telegram-bot.service`

2. **Database connection error:**
   - Check PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify credentials: `psql -h localhost -U botuser -d telegram_bot_db -W`

3. **Missing dependencies:**
   ```bash
   cd ~/telegram-bot
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart telegram-bot.service
   ```

### Can't SSH to Server?

1. Check security list has port 22 open
2. Verify key permissions: `chmod 400 telegram-bot-key.key`
3. Try with verbose mode: `ssh -v -i telegram-bot-key.key ubuntu@YOUR_IP`

### Oracle Might Reclaim Idle Instances

**Important:** Oracle may reclaim free instances with <10% CPU usage over 7 days.

**Solution - Keep instance active:**
```bash
# Create a simple cron job
crontab -e

# Add this line (runs every 5 minutes):
*/5 * * * * curl -s http://localhost > /dev/null
```

---

## 📚 Additional Resources

- **Oracle Cloud Docs:** https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm
- **python-telegram-bot Docs:** https://docs.python-telegram-bot.org/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/

---

## 🆘 Need Help?

If you encounter issues:

1. **Check bot logs:** `sudo journalctl -u telegram-bot.service -f`
2. **Check PostgreSQL:** `sudo systemctl status postgresql`
3. **Check system resources:** `htop` and `df -h`
4. **Verify firewall rules** in both Oracle Cloud and Ubuntu

---

## 🔒 Security Best Practices

1. **Change default SSH port** (optional but recommended)
2. **Set up automatic security updates:**
   ```bash
   sudo apt install unattended-upgrades -y
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```
3. **Enable firewall:**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
4. **Regular backups** of database
5. **Monitor logs** regularly for suspicious activity

---

**🎊 Congratulations! Your bot is now live 24/7 on Oracle Cloud Free Tier!**

No UptimeRobot needed - this is true always-on hosting! 🚀
