# Telegram Anonymous Chat Bot

## Overview
This is a completely rewritten Python-based Telegram bot that facilitates anonymous chat sessions between users. The bot has been enhanced with database persistence, admin controls, and improved user experience.

## Current Status
- ✅ Python 3.11 environment setup
- ✅ PostgreSQL database integration
- ✅ Complete bot rewrite with new features
- ✅ Admin control panel implemented
- ✅ Railway and Heroku deployment ready
- ✅ Enhanced privacy and security features
- ✅ Comprehensive button navigation system

## Latest Update (December 15, 2025) ✨
### NEW FEATURES:
1. **🌐 Language Selection (Sinhala & English)**:
   - Users can select language from Profile menu
   - Sinhala translations added for key messages
   - Language preference saved in database

2. **🎨 Sticker Support**:
   - Stickers now forward to chat partners
   - Protected content enabled for stickers

3. **📢 Improved Admin Broadcast**:
   - Added Cancel Broadcast button
   - Better broadcast flow management

## Previous Update (October 12, 2025) ✨
### NEW CREATIVE FEATURES ADDED:
1. **🎮 Interactive Games System**:
   - Would You Rather - Fun choice-based questions
   - Truth or Dare - Classic party game
   - Two Truths & A Lie - Icebreaker game

2. **🎁 Virtual Gifts System**:
   - 15+ unique virtual gifts (Rose, Heart, Star, Pizza, Coffee, etc.)
   - Send gifts to chat partners
   - Personalized gift messages

3. **💡 Social Features**:
   - Icebreakers - Random conversation starters (15+ questions)
   - Compliments - Send random compliments to partners
   - Fun Facts - Share interesting facts (10+ facts)
   - Daily Topics - Conversation topic suggestions (15+ topics)

4. **😊 Mood System**:
   - Set and display current mood/vibe
   - 10 mood options (Happy, Cool, Energetic, etc.)
   - Persisted in database
   - Shows in user profile

5. **📱 Enhanced UI/UX**:
   - Complete redesigned chat controls with game/gift buttons
   - Intuitive inline keyboards for all features
   - Clean navigation between features

6. **🚀 Vercel Deployment Support**:
   - Complete webhook-mode implementation
   - Serverless function ready (`api/webhook.py`)
   - Step-by-step deployment guide
   - Automatic HTTPS support

### BUG FIXES:
- Fixed missing `start_matching_with_retry` method
- Fixed None type checks in report system
- Cleaned up duplicate dependencies
- Added mood field to database schema

## Major Changes (September 18, 2025)
### Core Features Implemented:
1. **Simplified Matching**: Removed complex gender preference matching - only user gender selection
2. **Retry Matching**: Automatic retry system when no partners available (12 attempts over 2 minutes)
3. **Enhanced Profiles**: Users can set bio, age, location, and interests
4. **Admin System**: Full admin control panel for user management
5. **Database Persistence**: PostgreSQL integration for user data and session management
6. **Privacy Protection**: Screenshot blocking and content warnings
7. **Button Navigation**: Complete inline keyboard system
8. **Broadcasting**: Admin can broadcast messages to all users
9. **Warning System**: Removed profanity filter, added content warnings instead

### Database Schema:
- **Users**: Complete user profiles with ban system
- **Chat Sessions**: Persistent chat history and session tracking
- **Admin Actions**: Audit log for all admin activities
- **User Reports**: Report system with admin review
- **Broadcast Messages**: Message broadcasting with statistics

## Project Architecture
- **Main File**: `anonymous_chat_bot.py` - Complete bot implementation
- **Database**: `database.py` - SQLAlchemy models and database operations
- **Dependencies**: Enhanced with database support
- **Runtime**: Python 3.11
- **Database**: PostgreSQL with persistent storage

## Key Features
- **Simple Registration**: Only gender selection required
- **Smart Matching**: Random matching with retry system
- **Rich Profiles**: Bio, age, location, interests
- **Admin Controls**: Ban/unban, statistics, broadcasting
- **Privacy First**: No message storage, screenshot protection
- **Button Interface**: Complete navigation via inline keyboards
- **Content Moderation**: Warning system instead of blocking
- **Session Management**: Persistent chat session tracking

## Environment Variables Required
- `TELEGRAM_BOT_TOKEN`: Bot token from Telegram BotFather
- `DATABASE_URL`: PostgreSQL connection string (automatically provided)

## Admin Features (ID: 1395596220)
- Ban/unban users
- Broadcast messages to all users
- View bot statistics
- Review user reports
- Monitor system activity

## Bot Commands
- `/start` - Register/login and show main menu
- `/find` - Find a chat partner with retry system
- `/skip` - Skip current partner and find new one
- `/stop` - End current chat session
- `/report` - Report inappropriate behavior
- `/profile` - View/edit user profile
- `/help` - Complete help system with buttons
- `/privacy` - Privacy and safety information
- `/admin` - Admin panel (admin only)

## Deployment Ready
- **Replit**: Built-in deployment (recommended)
- **Railway**: `railway.toml` configuration
- **Heroku**: `Procfile` and `runtime.txt` configuration
- **Vercel**: `vercel.json` + webhook mode (`api/webhook.py`)
- **Requirements**: Clean dependency list
- **Database**: Automatic table creation
- **Documentation**: Comprehensive guides for each platform

## Technical Improvements
- Database persistence for all user data
- Async/await pattern throughout
- Proper error handling and logging
- Admin audit trail
- Content warning system
- Retry mechanism for matching
- Session management
- Privacy protection features