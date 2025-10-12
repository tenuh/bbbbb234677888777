# 🎭 Telegram Anonymous Chat Bot

A feature-rich anonymous chat bot built with Python and the Telegram Bot API. Connect with strangers worldwide, play games, share gifts, and have meaningful conversations—all while staying completely anonymous!

## ✨ Features

### 🎪 Core Features
- **🎲 Random Matching**: Get paired with random users for anonymous chat sessions
- **🎭 Unique Nicknames**: Each user gets a unique pseudonym for anonymity
- **👥 Gender Selection**: Choose your gender during registration
- **⏭️ Skip & Search**: Skip partners and find new matches instantly
- **🔒 Privacy First**: No message storage, screenshot protection, content warnings
- **👤 Rich Profiles**: Bio, age, location, interests, and mood status

### 🎮 Interactive Features
- **🎮 Fun Games**: 
  - Would You Rather
  - Truth or Dare
  - Two Truths & A Lie
- **🎁 Virtual Gifts**: Send 15+ different virtual gifts to your partner
- **💡 Icebreakers**: Random conversation starter questions
- **💬 Compliments**: Send random compliments to break the ice
- **🎯 Fun Facts**: Share interesting facts to keep conversations flowing
- **📅 Daily Topics**: Get conversation topics when you're stuck
- **😊 Mood System**: Set and display your current mood/vibe

### 🛡️ Safety & Moderation
- **🚨 Report System**: Report inappropriate behavior
- **⚠️ Content Warnings**: Automatic content moderation
- **🔨 Ban System**: Admin tools for user management
- **📊 Admin Panel**: Complete moderation dashboard
- **📢 Broadcasting**: Admin announcements to all users

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Quick Start (Local Development)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd telegram-anonymous-chat-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export DATABASE_URL="postgresql://user:pass@localhost/dbname"
   ```

4. **Run the bot**
   ```bash
   python anonymous_chat_bot.py
   ```

## 🚀 Deployment

For production deployment, we have detailed guides for each platform:

- ✅ **[Replit](DEPLOYMENT.md#replit-deployment)** - Easiest, recommended for beginners
- ✅ **[Railway](DEPLOYMENT.md#railway-deployment)** - Great for production
- ✅ **[Heroku](DEPLOYMENT.md#heroku-deployment)** - Classic choice
- ✅ **[Vercel](VERCEL_DEPLOYMENT.md)** - Serverless deployment (webhook mode)

### Quick Deploy Options:

**Quick Deploy:** Click the buttons below:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=...)
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## 📱 Bot Commands

### User Commands
- `/start` - Register and access main menu
- `/find` - Find a random chat partner
- `/skip` - Skip current partner, find new one
- `/stop` - End current chat session
- `/profile` - View/edit your profile
- `/help` - Show help menu
- `/privacy` - Privacy and safety info

### Admin Commands (Admin ID: 1395596220)
- `/admin` - Access admin panel
- Ban/unban users
- View reports and statistics
- Broadcast messages

## 🎮 How to Use

1. **Start the bot** - Send `/start` to begin
2. **Choose gender** - Select male or female
3. **Find a partner** - Click "Find Partner" to match with someone
4. **Chat & Play** - Use the interactive features:
   - 🎮 Play games together
   - 🎁 Send virtual gifts
   - 💡 Use icebreakers
   - 💬 Send compliments
5. **Skip or End** - Skip to find someone new or end the chat

## 🛠️ Tech Stack

- **Language**: Python 3.11
- **Bot Framework**: python-telegram-bot 20.7
- **Database**: PostgreSQL with SQLAlchemy
- **Deployment**: Railway, Heroku, or Replit

## 🔧 Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | ✅ Yes |
| `DATABASE_URL` | PostgreSQL connection URL | ✅ Yes |

### Admin Configuration
Update the `ADMIN_ID` in `anonymous_chat_bot.py`:
```python
ADMIN_ID = 1395596220  # Replace with your Telegram user ID
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

