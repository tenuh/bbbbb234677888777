# Telegram Anonymous Chat Bot

## Overview
This is a Python-based Telegram bot that facilitates anonymous chat sessions between users. The bot connects users based on gender preferences and includes features like pseudonyms, interest matching, content filtering, and the ability to skip conversations.

## Current Status
- ✅ Python 3.11 environment setup
- ✅ Dependencies installed (python-telegram-bot==20.7)
- ✅ Workflow configured and running
- ✅ Security improvements (environment variable for bot token)
- ✅ Project structure organized

## Recent Changes (September 18, 2025)
- Imported GitHub project to Replit environment
- Installed Python 3.11 and required dependencies
- Enhanced security by using environment variables for bot token instead of hardcoded values
- Created proper .gitignore for Python project
- Set up workflow to run the bot application

## Project Architecture
- **Main File**: `anonymous_chat_bot.py` - Core bot logic and handlers
- **Dependencies**: Python Telegram Bot API (v20.7)
- **Runtime**: Python 3.11
- **Type**: Backend application (Telegram bot)

## Key Features
- Random user pairing based on gender preferences
- Anonymous chat with unique pseudonyms
- Interest-based matching system
- Content filtering for inappropriate language
- Session management (skip, end chat, report)
- Real-time message forwarding between matched users

## Environment Variables
- `TELEGRAM_BOT_TOKEN`: Required bot token from Telegram BotFather

## Workflow Configuration
- **Name**: "Telegram Bot"
- **Command**: `python anonymous_chat_bot.py`
- **Output**: Console logging
- **Status**: Running and operational

## Commands Available in Bot
- `/start` - Initialize bot and select gender
- `/skip` - Skip current chat partner
- `/endchat` - End current chat session
- `/report` - Report inappropriate behavior
- `/interests` - Set personal interests for better matching

## Technical Notes
- Uses polling method to receive Telegram updates
- In-memory storage for user data and active sessions
- Gender-based queue system for user matching
- Interest intersection algorithm for optimal pairing
- Profanity filter with configurable word list