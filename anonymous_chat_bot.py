import logging
import os
import asyncio
import time
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Union

from telegram import (
  Update,
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  Message,
  BotCommand
)
from telegram.ext import (
  Application,
  CommandHandler,
  ContextTypes,
  MessageHandler,
  filters,
  CallbackQueryHandler,
  ConversationHandler
)
from telegram.error import TelegramError

import database
from database import (
  ensure_saved_chats_table,
  add_saved_chat,
  get_saved_chats,
  remove_saved_chat,
  count_saved_chats,
  is_chat_already_saved
)

# Configure logging
logging.basicConfig(
  format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level = logging.INFO
)
logger = logging.getLogger(__name__)

# Suppress sensitive HTTP logs that contain bot token
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

# Configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = 1395596220 # Fixed admin ID
RETRY_MATCHING_INTERVAL = 10 # seconds between matching retries
MAX_RETRY_ATTEMPTS = 12 # Maximum retry attempts (2 minutes)

if not TOKEN:
logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

# Conversation states
PROFILE_NAME, PROFILE_AGE, PROFILE_BIO, PROFILE_LOCATION, PROFILE_INTERESTS = range(5)
ADMIN_BROADCAST_MESSAGE, ADMIN_BAN_USER, ADMIN_UNBAN_USER = range(3)

# Translations
TRANSLATIONS = {
  'en': {
    'WELCOME': """🎭 **Welcome to Anonymous Chat Bot!**

Connect with people around the world anonymously and safely.

Choose your gender to get started:""",
    'LANG_SELECT': """🌐 **Select Language**

Choose your preferred language:""",
    'LANG_CHANGED': "✅ Language changed to English!",
    'MALE': "👨 Male",
    'FEMALE': "👩 Female",
    'FIND_PARTNER': "🔍 Find Partner",
    'MY_PROFILE': "👤 My Profile",
    'HELP': "❓ Help",
    'SETTINGS': "⚙️ Settings",
    'LANGUAGE': "🌐 Language",
    'SKIP': "⏭️ Skip",
    'STOP': "⏹️ Stop Chat",
    'REPORT': "🚨 Report",
    'GAMES': "🎮 Games",
    'GIFTS': "🎁 Gifts",
    'ICEBREAKER': "💡 Icebreaker",
    'BACK': "🔙 Back",
    'CANCEL': "❌ Cancel",
    'ALREADY_IN_CHAT': "❌ You're already in a chat! Use the buttons below to manage your session.",
    'ALREADY_WAITING': "⏳ You're already in the matching queue. Please wait...",
    'GENDER_SET': """✅ **Profile Created!**

🎭 **Nickname:** {}
👤 **Gender:** {}

Your profile is ready! Use the menu below to start chatting or customize your profile further.""",
    'CHAT_ENDED': "💬 Chat session ended. Use /start or the menu to begin a new chat!",
    'CHAT_ENDED_BY_PARTNER': "😔 Your chat partner ended the session.",
    'NOT_IN_CHAT': "❌ You're not in a chat session. Use /start to begin!",
    'SKIPPED_CHAT': "⏭️ Searching for a new chat partner...",
    'PARTNER_SKIPPED': "💔 Your partner found someone new. Let's find you a new partner!",
    'REPORT_SENT': "✅ Report submitted successfully. We'll review this. The chat has been ended.",
    'REPORT_ONLY_IN_CHAT': "⚠️ You can only report users during an active chat.",
    'MATCHING_STARTED': "🔍 **Searching for a chat partner...**\n\nWe're looking for someone to chat with. Use the buttons below to control your search.",
    'PARTNER_FOUND': "🎉 **Connected with {}!** \n\nStart chatting now. Be respectful and have fun!",
    'NO_PARTNER_FOUND': "😔 **No chat partner found right now.**\n\nThere might not be anyone available at the moment. Try refreshing or check back later!",
    'SEARCH_STOPPED': "⏹️ **Search stopped.**\n\nYou can start a new search anytime using the menu below.",
    'PROFILE_UPDATED': "✅ Profile updated successfully!",
    'WARNING_MESSAGE': "⚠️ **Content Warning**\n\nYour message may contain inappropriate content. Please be respectful in your conversations.",
    'REFRESH': "🔄 Refresh",
    'STOP_SEARCH': "⏹️ Stop Search",
  },
  'si': {
    'WELCOME': """🎭 **නිර්නාමික චැට් බොට් වෙත සාදරයෙන් පිළිගනිමු!**

ලොව පුරා සිටින අය සමඟ නිර්නාමිකව සහ ආරක්ෂිතව සම්බන්ධ වන්න.

ආරම්භ කිරීමට ඔබේ ස්ත්‍රී පුරුෂ භාවය තෝරන්න:""",
    'LANG_SELECT': """🌐 **භාෂාව තෝරන්න**

ඔබේ කැමති භාෂාව තෝරන්න:""",
    'LANG_CHANGED': "✅ භාෂාව සිංහල වෙත වෙනස් කරන ලදී!",
    'MALE': "👨 පිරිමි",
    'FEMALE': "👩 ගැහැණු",
    'FIND_PARTNER': "🔍 සහකරු සොයන්න",
    'MY_PROFILE': "👤 මගේ පැතිකඩ",
    'HELP': "❓ උදව්",
    'SETTINGS': "⚙️ සැකසුම්",
    'LANGUAGE': "🌐 භාෂාව",
    'SKIP': "⏭️ මඟහරින්න",
    'STOP': "⏹️ චැට් නවත්වන්න",
    'REPORT': "🚨 වාර්තා කරන්න",
    'GAMES': "🎮 ක්‍රීඩා",
    'GIFTS': "🎁 තෑගි",
    'ICEBREAKER': "💡 අයිස් බ්‍රේකර්",
    'BACK': "🔙 ආපසු",
    'CANCEL': "❌ අවලංගු කරන්න",
    'ALREADY_IN_CHAT': "❌ ඔබ දැනටමත් චැට් එකක සිටී! ඔබේ සැසිය කළමනාකරණය කිරීමට පහත බොත්තම් භාවිතා කරන්න.",
    'ALREADY_WAITING': "⏳ ඔබ දැනටමත් පෙළගැස්මේ සිටී. කරුණාකර රැඳී සිටින්න...",
    'GENDER_SET': """✅ **පැතිකඩ සාදන ලදී!**

🎭 **අන්වර්ථ නාමය:** {}
👤 **ස්ත්‍රී පුරුෂ භාවය:** {}

ඔබේ පැතිකඩ සූදානම්! චැට් කිරීම ආරම්භ කිරීමට හෝ ඔබේ පැතිකඩ වැඩිදුරටත් අභිරුචිකරණය කිරීමට පහත මෙනුව භාවිතා කරන්න.""",
    'CHAT_ENDED': "💬 චැට් සැසිය අවසන් විය. නව චැට් එකක් ආරම්භ කිරීමට /start හෝ මෙනුව භාවිතා කරන්න!",
    'CHAT_ENDED_BY_PARTNER': "😔 ඔබේ චැට් සහකරු සැසිය අවසන් කළේය.",
    'NOT_IN_CHAT': "❌ ඔබ චැට් සැසියක නැත. ආරම්භ කිරීමට /start භාවිතා කරන්න!",
    'SKIPPED_CHAT': "⏭️ නව චැට් සහකරුවෙකු සොයමින්...",
    'PARTNER_SKIPPED': "💔 ඔබේ සහකරු අලුත් කෙනෙකු සොයාගත්තා. අපි ඔබට නව සහකරුවෙකු සොයමු!",
    'REPORT_SENT': "✅ වාර්තාව සාර්ථකව ඉදිරිපත් කරන ලදී. අපි මෙය සමාලෝචනය කරන්නෙමු. චැට් එක අවසන් කර ඇත.",
    'REPORT_ONLY_IN_CHAT': "⚠️ ඔබට ක්‍රියාකාරී චැට් එකක් තුළ පමණක් පරිශීලකයින් වාර්තා කළ හැක.",
    'MATCHING_STARTED': "🔍 **චැට් සහකරුවෙකු සොයමින්...**\n\nඅපි චැට් කිරීමට යමෙකු සොයමින් සිටිමු. ඔබේ සෙවුම පාලනය කිරීමට පහත බොත්තම් භාවිතා කරන්න.",
    'PARTNER_FOUND': "🎉 **{} සමඟ සම්බන්ධ විය!** \n\nදැන් චැට් කිරීම ආරම්භ කරන්න. ගෞරවාන්විතව සිට විනෝද වන්න!",
    'NO_PARTNER_FOUND': "😔 **මේ මොහොතේ චැට් සහකරුවෙකු හමු නොවීය.**\n\nදැන් කිසිවෙකු නොතිබිය හැක. නැවුම් කිරීමට උත්සාහ කරන්න හෝ පසුව නැවත පරීක්ෂා කරන්න!",
    'SEARCH_STOPPED': "⏹️ **සෙවීම නතර විය.**\n\nඔබට ඕනෑම වේලාවක පහත මෙනුව භාවිතයෙන් නව සෙවීමක් ආරම්භ කළ හැක.",
    'PROFILE_UPDATED': "✅ පැතිකඩ සාර්ථකව යාවත්කාලීන කරන ලදී!",
    'WARNING_MESSAGE': "⚠️ **අන්තර්ගත අනතුරු ඇඟවීම**\n\nඔබේ පණිවිඩයේ නුසුදුසු අන්තර්ගතයක් අඩංගු විය හැක. කරුණාකර ඔබේ සංවාදවල ගෞරවාන්විතව සිටින්න.",
    'REFRESH': "🔄 නැවුම් කරන්න",
    'STOP_SEARCH': "⏹️ සෙවීම නවත්වන්න",
  }
}

def get_text(key: str, lang: str = 'en') -> str:
"""Get translated text for given key and language"""
if lang not in TRANSLATIONS:
lang = 'en'
return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, TRANSLATIONS['en'].get(key, key))

def get_user_lang(db, user_id: int) -> str:
"""Get user's preferred language from database"""
user = database.get_user(db, user_id)
if user and user.language:
return user.language
return 'en'

# Messages and UI
class Messages:
WELCOME = """🎭 **Welcome to Anonymous Chat Bot!**

Connect with people around the world anonymously and safely.

Choose your gender to get started:"""

PROFILE_CREATION = """📋 **Create Your Profile**

Let's set up your profile for better matching and conversations."""

ALREADY_IN_CHAT = "❌ You're already in a chat! Use the buttons below to manage your session."
ALREADY_WAITING = "⏳ You're already in the matching queue. Please wait..."

GENDER_SET = """✅ **Profile Created!**

🎭 **Nickname:** {}
👤 **Gender:** {}

Your profile is ready! Use the menu below to start chatting or customize your profile further."""

CHAT_ENDED = "💬 Chat session ended. Use /start or the menu to begin a new chat!"
CHAT_ENDED_BY_PARTNER = "😔 Your chat partner ended the session."
NOT_IN_CHAT = "❌ You're not in a chat session. Use /start to begin!"

SKIPPED_CHAT = "⏭️ Searching for a new chat partner..."
PARTNER_SKIPPED = "💔 Your partner found someone new. Let's find you a new partner!"

REPORT_SENT = "✅ Report submitted successfully. We'll review this. The chat has been ended."
REPORT_ONLY_IN_CHAT = "⚠️ You can only report users during an active chat."

MATCHING_STARTED = "🔍 **Searching for a chat partner...**\n\nWe're looking for someone to chat with. Use the buttons below to control your search."
PARTNER_FOUND = "🎉 **Connected with {}!** \n\nStart chatting now. Be respectful and have fun!"

NO_PARTNER_FOUND = "😔 **No chat partner found right now.**\n\nThere might not be anyone available at the moment. Try refreshing or check back later!"
SEARCH_STOPPED = "⏹️ **Search stopped.**\n\nYou can start a new search anytime using the menu below."

PROFILE_UPDATED = "✅ Profile updated successfully!"
PROFILE_INFO = """👤 **Your Profile**

🎭 **Nickname:** {}
👤 **Gender:** {}
😊 **Mood:** {}
📝 **Bio:** {}
🎂 **Age:** {}
📍 **Location:** {}
💭 **Interests:** {}
📅 **Member Since:** {}"""

WARNING_MESSAGE = "⚠️ **Content Warning**\n\nYour message may contain inappropriate content. Please be respectful in your conversations."

HELP_MENU = """❓ **Help & Commands**

🎭 **Chat Commands:**
• `/start` - Start the bot and begin matching
• `/find` - Find a random chat partner
• `/skip` - Find a new chat partner
• `/stop` - End current chat session
• `/report` - Report inappropriate behavior

🎮 **Fun Features During Chat:**
• 🎮 Play Games - Would You Rather, Truth or Dare, Two Truths & A Lie
• 🎁 Send Gifts - Send virtual gifts to your partner
• 💡 Icebreakers - Get conversation starter questions
• 💬 Compliments - Send random compliments
• 🎯 Fun Facts - Share interesting facts
• 📅 Daily Topics - Get conversation topics

👤 **Profile:**
• `/profile` - View/edit your profile
• `/interests` - Set your interests
• 😊 Set Mood - Show your current vibe

📋 **General:**
• `/help` - Show this help menu
• `/privacy` - Privacy information

Use the buttons below for easy navigation!"""

PRIVACY_INFO = """🔒 **Privacy & Safety**

**Your Privacy:**
• All chats are completely anonymous
• We don't store your chat messages
• Screenshots are automatically blocked
• Only your basic profile info is stored

**Safety Features:**
• Report inappropriate behavior anytime
• Automatic moderation and warnings
• Ban system for repeat offenders
• Admin oversight for serious issues

**Tips:**
• Be respectful to other users
• Don't share personal information
• Use the report feature if needed
• Have fun and stay safe!"""

ADMIN_PANEL = """👑 **Admin Panel**

**User Management:**
• Ban/Unban users
• View user reports
• Broadcast messages

**Statistics:**
• Active users
• Total chats today
• Reports pending

Use the buttons below:"""

SCREENSHOT_BLOCKED = "📷 **Screenshot Detected!**\n\nFor privacy protection, screenshots are not allowed in this bot. Please respect other users' privacy."

# Creative Features Data
class IceBreakers:
QUESTIONS = [
  "If you could have dinner with anyone from history, who would it be?",
  "What's the most adventurous thing you've ever done?",
  "If you could live anywhere in the world, where would it be?",
  "What's your favorite way to spend a weekend?",
  "If you could have any superpower, what would it be and why?",
  "What's the best piece of advice you've ever received?",
  "If you could master any skill instantly, what would it be?",
  "What's your dream job?",
  "If you could travel back in time, which era would you visit?",
  "What's something you're passionate about?",
  "If you could only eat one food for the rest of your life, what would it be?",
  "What's the coolest place you've ever visited?",
  "If you won the lottery tomorrow, what's the first thing you'd do?",
  "What's your favorite book or movie and why?",
  "If you could change one thing about the world, what would it be?",
]

class Games:
WOULD_YOU_RATHER = [
  "Would you rather: Have the ability to fly OR be invisible?",
  "Would you rather: Time travel to the past OR to the future?",
  "Would you rather: Live in the mountains OR by the beach?",
  "Would you rather: Never use social media again OR never watch another movie/TV show?",
  "Would you rather: Have unlimited money OR unlimited free time?",
  "Would you rather: Be able to speak every language OR play every instrument?",
  "Would you rather: Live without music OR without movies?",
  "Would you rather: Always be 10 minutes late OR 20 minutes early?",
  "Would you rather: Read minds OR predict the future?",
  "Would you rather: Have a rewind button OR a pause button for your life?",
]

TRUTH_OR_DARE = {
  'truth': [
    "What's your biggest fear?",
    "What's the most embarrassing thing that's happened to you?",
    "What's your biggest regret?",
    "Who was your first crush?",
    "What's a secret talent you have?",
    "What's your guilty pleasure?",
    "What's the craziest dream you've ever had?",
    "If you could change one thing about yourself, what would it be?",
  ],
  'dare': [
    "Send a funny GIF or meme to your partner",
    "Tell your partner a joke",
    "Share your most unpopular opinion",
    "Describe your perfect day",
    "Send 5 emojis that describe you",
    "Tell your partner a fun fact about yourself",
    "Share your favorite song right now",
    "Describe yourself in 3 words",
  ]
}

TWO_TRUTHS_LIE = [
  "Share 2 truths and 1 lie about yourself - your partner has to guess the lie!",
  "Tell your partner 3 facts about you (2 true, 1 false) and see if they can spot the lie!",
]

class VirtualGifts:
GIFTS = {
  '🌹': 'Rose',
  '🎁': 'Gift',
  '⭐': 'Star',
  '❤️': 'Heart',
  '🍕': 'Pizza',
  '🍰': 'Cake',
  '☕': 'Coffee',
  '🎵': 'Music',
  '🌈': 'Rainbow',
  '🔥': 'Fire',
  '💎': 'Diamond',
  '🏆': 'Trophy',
  '🎨': 'Art',
  '📚': 'Book',
  '🌟': 'Sparkle',
}

class Compliments:
LIST = [
  "You seem like a really interesting person! 🌟",
  "Your conversation skills are amazing! 💬",
  "You have a great sense of humor! 😄",
  "You're really easy to talk to! ✨",
  "I appreciate your perspective on things! 🎯",
  "You bring good vibes to this chat! ☀️",
  "You're a great conversationalist! 💫",
  "Your positivity is contagious! 🌈",
  "You have interesting thoughts! 💭",
  "Chatting with you is fun! 🎉",
]

class FunFacts:
FACTS = [
  "🐙 Octopuses have three hearts!",
  "🍯 Honey never spoils - archaeologists found 3000-year-old honey that's still edible!",
  "🦘 Kangaroos can't walk backwards!",
  "🌙 A day on Venus is longer than its year!",
  "🐘 Elephants can't jump!",
  "🦋 Butterflies taste with their feet!",
  "🍌 Bananas are berries, but strawberries aren't!",
  "🐌 Snails can sleep for 3 years!",
  "⚡ Lightning is 5 times hotter than the sun!",
  "🧠 Your brain uses 20% of your body's energy!",
]

class DailyTopics:
TOPICS = [
  "🎬 Movies & TV Shows",
  "🎮 Gaming & Entertainment",
  "🌍 Travel & Adventure",
  "🎨 Art & Creativity",
  "📚 Books & Literature",
  "🎵 Music & Artists",
  "🍕 Food & Cooking",
  "💼 Dreams & Aspirations",
  "🏃 Sports & Fitness",
  "🔬 Science & Technology",
  "🌱 Nature & Environment",
  "📸 Photography & Memories",
  "🎭 Life Experiences",
  "🤔 Philosophy & Deep Thoughts",
  "😄 Funny Stories & Jokes",
]

class Moods:
OPTIONS = {
  '😊': 'Happy',
  '😎': 'Cool',
  '🤔': 'Thoughtful',
  '😴': 'Sleepy',
  '🎉': 'Excited',
  '😌': 'Chill',
  '🔥': 'Energetic',
  '💭': 'Contemplative',
  '🌟': 'Inspired',
  '🎵': 'Musical',
}

class Keyboards:
@staticmethod
def gender_selection():
return InlineKeyboardMarkup([
  [InlineKeyboardButton("👨 Male", callback_data = 'gender_male')],
  [InlineKeyboardButton("👩 Female", callback_data = 'gender_female')]
])

@staticmethod
def main_menu():
return InlineKeyboardMarkup([
  [InlineKeyboardButton("💬 Find Partner", callback_data = 'find_partner')],
  [InlineKeyboardButton("👤 My Profile", callback_data = 'view_profile'),
    InlineKeyboardButton("❓ Help", callback_data = 'help_menu')],
  [InlineKeyboardButton("🔒 Privacy", callback_data = 'privacy_info')]
])

@staticmethod
def chat_controls():
return InlineKeyboardMarkup([
  [InlineKeyboardButton("🎁 Send Gift", callback_data = 'send_gift'),
    InlineKeyboardButton("💬 Compliment", callback_data = 'send_compliment')],
  [InlineKeyboardButton("👤 View Profile", callback_data = 'view_partner_profile')],
  [InlineKeyboardButton("💾 Save Chat", callback_data = 'save_chat')],
  [InlineKeyboardButton("⏭️ Skip Chat", callback_data = 'skip_chat')],
  [InlineKeyboardButton("❌ End Chat", callback_data = 'end_chat')],
  [InlineKeyboardButton("🚨 Report", callback_data = 'report_user')]
])

@staticmethod
def games_menu():
return InlineKeyboardMarkup([
  [InlineKeyboardButton("🤔 Would You Rather", callback_data = 'game_wyr')],
  [InlineKeyboardButton("🎲 Truth or Dare", callback_data = 'game_tod')],
  [InlineKeyboardButton("🎭 Two Truths & A Lie", callback_data = 'game_ttal')],
  [InlineKeyboardButton("🔙 Back to Chat", callback_data = 'back_to_chat')]
])

@staticmethod
def truth_or_dare():
return InlineKeyboardMarkup([
  [InlineKeyboardButton("✨ Truth", callback_data = 'tod_truth')],
  [InlineKeyboardButton("🔥 Dare", callback_data = 'tod_dare')],
  [InlineKeyboardButton("🔙 Back", callback_data = 'games_menu')]
])

@staticmethod
@staticmethod
def virtual_gifts():
    buttons = []
    gifts = list(VirtualGifts.GIFTS.items())

    for i in range(0, len(gifts), 3):
        row = [
            InlineKeyboardButton(
                f"{emoji} {name}",
                callback_data=f"gift_{emoji}"
            )
            for emoji, name in gifts[i:i+3]
        ]
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("🔙 Back to Chat", callback_data='back_to_chat')
    ])

    return InlineKeyboardMarkup(buttons)


@staticmethod
@staticmethod
def mood_selector():
    buttons = []
    moods = list(Moods.OPTIONS.items())

    for i in range(0, len(moods), 3):
        row = [
            InlineKeyboardButton(
                f"{emoji} {name}",
                callback_data=f"mood_{emoji}"
            )
            for emoji, name in moods[i:i+3]
        ]
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("🔙 Back", callback_data='view_profile')
    ])

    return InlineKeyboardMarkup(buttons)


@staticmethod
def profile_menu():
return InlineKeyboardMarkup([
  [InlineKeyboardButton("✏️ Edit Profile", callback_data = 'edit_profile')],
  [InlineKeyboardButton("💭 Set Interests", callback_data = 'set_interests')],
  [InlineKeyboardButton("😊 Set Mood", callback_data = 'set_mood')],
  [InlineKeyboardButton("🌐 Language", callback_data = 'change_language')],
  [InlineKeyboardButton("🔙 Back to Menu", callback_data = 'main_menu')]
])

@staticmethod
def language_selection():
return InlineKeyboardMarkup([
  [InlineKeyboardButton("🇬🇧 English", callback_data = 'lang_en')],
  [InlineKeyboardButton("🇱🇰 සිංහල (Sinhala)", callback_data = 'lang_si')],
  [InlineKeyboardButton("🔙 Back", callback_data = 'view_profile')]
])

@staticmethod
def admin_panel():
return InlineKeyboardMarkup([
  [InlineKeyboardButton("👥 User Management", callback_data = 'admin_users')],
  [InlineKeyboardButton("📢 Broadcast", callback_data = 'admin_broadcast')],
  [InlineKeyboardButton("📊 Statistics", callback_data = 'admin_stats')],
  [InlineKeyboardButton("📝 Reports", callback_data = 'admin_reports')],
  [InlineKeyboardButton("🔙 Main Menu", callback_data = 'main_menu')]
])

@staticmethod
def help_navigation():
return InlineKeyboardMarkup([
  [InlineKeyboardButton("💬 Start Chatting", callback_data = 'find_partner')],
  [InlineKeyboardButton("👤 Profile", callback_data = 'view_profile')],
  [InlineKeyboardButton("🔙 Main Menu", callback_data = 'main_menu')]
])

@staticmethod
def searching_controls():
return InlineKeyboardMarkup([
  [InlineKeyboardButton("🔄 Refresh Search", callback_data = 'refresh_search')],
  [InlineKeyboardButton("⏹️ Stop Search", callback_data = 'stop_search')],
  [InlineKeyboardButton("🔙 Main Menu", callback_data = 'main_menu')]
])

class MatchmakingService:
def __init__(self):
self.waiting_users: Set[int] = set()
self.active_sessions: Dict[int, int] = {} # user_id -> partner_id
self.retry_tasks: Dict[int, asyncio.Task] = {}
self.lock = asyncio.Lock()

async def add_to_queue(self, user_id: int) -> bool:
"""Add user to waiting queue"""
async with self.lock:
with database.get_db() as db:
user = database.get_user(db, user_id)
if not user or user.is_banned:
return False

if user_id in self.active_sessions or user_id in self.waiting_users:
return False

self.waiting_users.add(user_id)
database.update_user_activity(db, user_id)
return True

async def find_partner(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
"""Find a chat partner with retry logic"""
async with self.lock:
with database.get_db() as db:
user = database.get_user(db, user_id)
if not user:
return None

# Look for available partners (excluding self)
available_partners = [uid for uid in self.waiting_users if uid != user_id]

if not available_partners:
return None

# Simple random selection (no preference matching as requested)
partner_id = random.choice(available_partners)

# Remove both from queue
self.waiting_users.discard(user_id)
self.waiting_users.discard(partner_id)

# Create active session
self.active_sessions[user_id] = partner_id
self.active_sessions[partner_id] = user_id

# Create database session
database.create_chat_session(db, user_id, partner_id)

return partner_id

def end_session(self, user_id: int, partner_id: int):
"""End a chat session between two users"""
# Remove from active sessions
self.active_sessions.pop(user_id, None)
self.active_sessions.pop(partner_id, None)

async def notify_match(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, partner_id: int):
"""Notify both users about successful match and auto-delete search panels"""
with database.get_db() as db:
user = database.get_user(db, user_id)
partner = database.get_user(db, partner_id)

if user and partner:
user_msg = Messages.PARTNER_FOUND.format(partner.nickname)
partner_msg = Messages.PARTNER_FOUND.format(user.nickname)

# Delete search messages for both users if they exist
for uid in [user_id, partner_id]:
search_msg_key = f"search_message_{user_id}"

if search_msg_key in context.user_data:
try:
msg_info = context.user_data[search_msg_key]
await context.bot.delete_message(
  chat_id = msg_info['chat_id'],
  message_id = msg_info['message_id']
)
except Exception as e:
logger.debug(f"Failed to delete search message for user {
  uid
}: {
  e
}")
finally:
context.user_data.pop(search_msg_key, None)

await context.bot.send_message(user_id, user_msg, reply_markup = Keyboards.chat_controls())
await context.bot.send_message(partner_id, partner_msg, reply_markup = Keyboards.chat_controls())

async def end_chat(self, user_id: int) -> Optional[int]:
"""End chat session"""
async with self.lock:
partner_id = self.active_sessions.pop(user_id, None)
if partner_id:
self.active_sessions.pop(partner_id, None)

# Update database
with database.get_db() as db:
session = database.get_active_chat_session(db, user_id)
if session:
database.end_chat_session(db, session.id, user_id)

return partner_id
return None

async def remove_from_queue(self, user_id: int):
"""Remove user from waiting queue"""
async with self.lock:
self.waiting_users.discard(user_id)
# Cancel retry task if exists
if user_id in self.retry_tasks:
self.retry_tasks[user_id].cancel()
del self.retry_tasks[user_id]

def get_partner(self, user_id: int) -> Optional[int]:
"""Get current chat partner"""
return self.active_sessions.get(user_id)

async def start_matching_with_retry(self, user_id: int, context: ContextTypes.DEFAULT_TYPE):
"""Start matching process with retry logic"""
attempts = 0
while attempts < MAX_RETRY_ATTEMPTS and user_id in self.waiting_users:
await asyncio.sleep(RETRY_MATCHING_INTERVAL)

partner_id = await self.find_partner(user_id, context)
if partner_id:
await self.notify_match(context, user_id, partner_id)
break

attempts += 1

if user_id in self.waiting_users and attempts >= MAX_RETRY_ATTEMPTS:
self.waiting_users.discard(user_id)
await context.bot.send_message(
  user_id,
  Messages.NO_PARTNER_FOUND,
  reply_markup = Keyboards.main_menu()
)

# Global service instance
matchmaking = MatchmakingService()

# Nicknames for users
NICKNAMES = [
  'Phoenix', 'Shadow', 'Storm', 'Raven', 'Wolf', 'Tiger', 'Lion', 'Eagle', 'Bear', 'Fox',
  'Cosmic', 'Nova', 'Star', 'Moon', 'Sun', 'Ocean', 'River', 'Mountain', 'Forest', 'Sky',
  'Crimson', 'Azure', 'Golden', 'Silver', 'Emerald', 'Ruby', 'Sapphire', 'Diamond', 'Pearl', 'Jade',
  'Thunder', 'Lightning', 'Blaze', 'Frost', 'Wind', 'Rain', 'Snow', 'Cloud', 'Mist', 'Dawn',
  'Mystic', 'Sage', 'Dream', 'Vision', 'Spirit', 'Soul', 'Heart', 'Mind', 'Zen', 'Peace'
]

def get_unique_nickname() -> str:
"""Get a unique nickname"""
with database.get_db() as db:
used_nicknames = {
  user.nickname for user in db.query(database.User).all()}
available = [n for n in NICKNAMES if n not in used_nicknames]
return random.choice(available if available else NICKNAMES)

def is_admin(user_id: int) -> bool:
"""Check if user is admin"""
return user_id == ADMIN_ID

def contains_inappropriate_content(text: str) -> bool:
"""Simple content filter that gives warnings instead of blocking"""
# Basic inappropriate content detection
inappropriate_patterns = [
r'\b(fuck|shit|bitch|asshole)\b',
r'\b(kill\s+yourself|kys)\b',
r'\b(suicide|rape|nazi|hitler)\b',
]

for pattern in inappropriate_patterns:
if re.search(pattern, text.lower()):
return True
return False

USERNAME_PATTERN = re.compile(r'@\w+')
PHONE_PATTERN = re.compile(r'@')
from telegram.ext import ApplicationHandlerStop

async def block_personal_info(update, context):
if not update.message or not update.message.text:
return

text = update.message.text

if USERNAME_PATTERN.search(text) or PHONE_PATTERN.search(text):
try:
await update.message.delete()
except:
pass

# stop ONLY blocked messages
raise ApplicationHandlerStop


async def handle_screenshot_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE):
"""Handle screenshot attempts (privacy protection)"""
await update.message.reply_text(Messages.SCREENSHOT_BLOCKED)

# Command Handlers


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle /start command"""
user_id = update.effective_user.id
telegram_user = update.effective_user

with database.get_db() as db:
user = database.get_user(db, user_id)

if user:
if user.is_banned:
await update.message.reply_text(
f"❌ **Account Suspended**\n\nYour account has been suspended.\n**Reason:** {
  user.ban_reason or 'Policy violation'
}\n\nContact support if you believe this is an error.",
  parse_mode = 'Markdown'
)
return

# Existing user - show main menu
database.update_user_activity(db, user_id)
partner = matchmaking.get_partner(user_id)

if partner:
await update.message.reply_text(Messages.ALREADY_IN_CHAT, reply_markup = Keyboards.chat_controls())
elif user_id in matchmaking.waiting_users:
await update.message.reply_text(Messages.ALREADY_WAITING)
else :
await update.message.reply_text(
f"👋 Welcome back, ** {
  user.nickname
}**!\n\nWhat would you like to do?",
  reply_markup = Keyboards.main_menu(),
  parse_mode = 'Markdown'
)
else :
# New user - start registration
await update.message.reply_text(
  Messages.WELCOME,
  reply_markup = Keyboards.gender_selection(),
  parse_mode = 'Markdown'
)

async def find_partner_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle /find command"""
await handle_find_partner(update, context)

async def handle_find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle partner finding"""
user_id = update.effective_user.id

with database.get_db() as db:
user = database.get_user(db, user_id)
if not user:
await update.message.reply_text("❌ Please register first using /start")
return

if user.is_banned:
await update.message.reply_text("❌ Your account is suspended.")
return

if matchmaking.get_partner(user_id):
await update.message.reply_text(Messages.ALREADY_IN_CHAT, reply_markup = Keyboards.chat_controls())
return

if user_id in matchmaking.waiting_users:
await update.message.reply_text(Messages.ALREADY_WAITING)
return

if await matchmaking.add_to_queue(user_id):
# Try to find partner immediately
partner_id = await matchmaking.find_partner(user_id, context)
if partner_id:
await matchmaking.notify_match(context, user_id, partner_id)
else :
await update.message.reply_text(
  Messages.MATCHING_STARTED,
  reply_markup = Keyboards.searching_controls()
)
else :
await update.message.reply_text("❌ Unable to start matching. Please try again.")

async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle /skip command"""
await handle_skip_chat(update, context)

async def handle_skip_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle skipping current chat"""
user_id = update.effective_user.id
partner_id = await matchmaking.end_chat(user_id)

if partner_id:
await update.message.reply_text(Messages.SKIPPED_CHAT)
await context.bot.send_message(partner_id, Messages.PARTNER_SKIPPED, reply_markup = Keyboards.main_menu())

# Start new search for current user
await handle_find_partner(update, context)
else :
await update.message.reply_text(Messages.NOT_IN_CHAT, reply_markup = Keyboards.main_menu())

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle /stop command"""
await handle_end_chat(update, context)

async def handle_end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle ending chat"""
user_id = update.effective_user.id
partner_id = await matchmaking.end_chat(user_id)
await matchmaking.remove_from_queue(user_id)

if partner_id:
await update.message.reply_text(Messages.CHAT_ENDED, reply_markup = Keyboards.main_menu())
await context.bot.send_message(partner_id, Messages.CHAT_ENDED_BY_PARTNER, reply_markup = Keyboards.main_menu())
else :
await update.message.reply_text(Messages.CHAT_ENDED, reply_markup = Keyboards.main_menu())

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle /report command"""
await handle_report_user(update, context)

async def handle_report_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle reporting current partner"""
user_id = update.effective_user.id
partner_id = matchmaking.get_partner(user_id)

if not partner_id:
await update.message.reply_text(Messages.REPORT_ONLY_IN_CHAT)
return

with database.get_db() as db:
session = database.get_active_chat_session(db, user_id)
database.create_user_report(
  db, user_id, partner_id,
  session.id if session else None,
  "Reported via bot command"
)

# End the chat
await matchmaking.end_chat(user_id)
await update.message.reply_text(Messages.REPORT_SENT, reply_markup = Keyboards.main_menu())

if partner_id:
await context.bot.send_message(partner_id, Messages.CHAT_ENDED_BY_PARTNER, reply_markup = Keyboards.main_menu())

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle /profile command"""
await show_profile(update, context)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Show user profile"""
user_id = update.effective_user.id

with database.get_db() as db:
user = database.get_user(db, user_id)
if not user:
await update.message.reply_text("❌ Please register first using /start")
return

interests = ", ".join([interest.name for interest in user.interests]) if user.interests else "None set"
created_date = user.created_at.strftime("%B %d, %Y")
mood_display = f" {
  user.mood
} {
  Moods.OPTIONS.get(user.mood, '')}" if user.mood else "Not set"

profile_text = Messages.PROFILE_INFO.format(
  user.nickname,
  user.gender.title(),
  mood_display,
  user.bio or "Not set",
  user.age or "Not set",
  user.location or "Not set",
  interests,
  user.total_chats,
  created_date
)

await update.message.reply_text(
  profile_text,
  reply_markup = Keyboards.profile_menu(),
  parse_mode = 'Markdown'
)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle /help command"""
await update.message.reply_text(
  Messages.HELP_MENU,
  reply_markup = Keyboards.help_navigation(),
  parse_mode = 'Markdown'
)

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle /privacy command"""
# Create privacy keyboard with back button
privacy_keyboard = InlineKeyboardMarkup([
  [InlineKeyboardButton("🔙 Back to Menu", callback_data = 'main_menu')]
])
await update.message.reply_text(
  Messages.PRIVACY_INFO,
  reply_markup = privacy_keyboard,
  parse_mode = 'Markdown'
)
async def saved_chats_command(update, context):

user_id = update.effective_user.id
saved = database.get_saved_chats(user_id)

if not saved:
await update.message.reply_text("📂 No saved chats.")
return

keyboard = []

for row in saved:
sid = row["saved_user_id"]

keyboard.append([
  InlineKeyboardButton("🔄 Reconnect", callback_data = f"reconnect_ {
    sid
  }"),
  InlineKeyboardButton("❌ Remove", callback_data = f"remove_saved_ {
    sid
  }")
])

await update.message.reply_text(
  "📂 Saved Chats:",
  reply_markup = InlineKeyboardMarkup(keyboard)
)

# Callback Query Handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle all button callbacks"""

query = update.callback_query
await query.answer()

user_id = query.from_user.id
data = query.data

# ===============================
# SAVED CHAT FEATURES
# ===============================

if data == "save_chat":

partner_id = matchmaking.get_partner(user_id)

if not partner_id:
await query.answer("❌ Not in chat", show_alert = True)
return

if database.count_saved_chats(user_id) >= 3:
await query.answer("❌ Max 3 saved chats", show_alert = True)
return

database.add_saved_chat(user_id, partner_id)
database.add_saved_chat(partner_id, user_id)

await query.answer("✅ Chat saved!")

elif data.startswith("reconnect_"):

target_id = int(data.split("_")[1])

keyboard = [[
  InlineKeyboardButton(
    "Accept",
    callback_data = f"accept_reconnect_ {
      user_id
    }"
  )
]]

await context.bot.send_message(
  target_id,
  "🔔 Someone wants to reconnect with you.",
  reply_markup = InlineKeyboardMarkup(keyboard)
)

await query.answer("Request sent!")

elif data.startswith("accept_reconnect_"):

requester = int(data.split("_")[-1])

old = matchmaking.get_partner(user_id)
if old:
matchmaking.end_session(user_id, old)

old = matchmaking.get_partner(requester)
if old:
matchmaking.end_session(requester, old)

matchmaking.active_sessions[user_id] = requester
matchmaking.active_sessions[requester] = user_id

await context.bot.send_message(user_id, "💬 Reconnected!")
await context.bot.send_message(requester, "💬 Reconnected!")

elif data.startswith("remove_saved_"):

target = int(data.split("_")[-1])

database.remove_saved_chat(user_id, target)

await query.answer("Removed")
await query.edit_message_text("❌ Saved chat removed.")

# ===============================
# GENDER SELECTION
# ===============================
# Gender selection
if data.startswith('gender_'):
await handle_gender_selection(query, context)

# Main navigation
elif data == 'find_partner':
await handle_find_partner_callback(query, context)

elif data == 'view_profile':
await show_profile_callback(query, context)

elif data == 'help_menu':
await query.edit_message_text(
  Messages.HELP_MENU,
  reply_markup = Keyboards.help_navigation(),
  parse_mode = 'Markdown'
)

elif data == 'privacy_info':
# Create privacy keyboard with back button
privacy_keyboard = InlineKeyboardMarkup([
  [InlineKeyboardButton("🔙 Back to Menu", callback_data = 'main_menu')]
])
await query.edit_message_text(Messages.PRIVACY_INFO, reply_markup = privacy_keyboard, parse_mode = 'Markdown')

elif data == 'main_menu':
with database.get_db() as db:
user = database.get_user(db, user_id)
if user:
await query.edit_message_text(
f"👋 Welcome back, ** {
  user.nickname
}**!\n\nWhat would you like to do?",
  reply_markup = Keyboards.main_menu(),
  parse_mode = 'Markdown'
)

# Chat controls
elif data == 'skip_chat':
await handle_skip_chat_callback(query, context)

elif data == 'end_chat':
await handle_end_chat_callback(query, context)

elif data == 'report_user':
await handle_report_user_callback(query, context)

elif data == 'back_to_chat':
await query.edit_message_text(
  "💬 **Back to Chat**\n\nYou can continue chatting. Use the buttons below:",
  reply_markup = Keyboards.chat_controls(),
  parse_mode = 'Markdown'
)

# Profile management
elif data == 'edit_profile':
await handle_edit_profile_callback(query, context)

elif data == 'set_interests':
await handle_set_interests_callback(query, context)

elif data.startswith('edit_'):
await handle_profile_edit_callback(query, context)

elif data.startswith('change_gender_'):
await handle_change_gender_callback(query, context)

elif data == 'view_partner_profile':
await handle_view_partner_profile_callback(query, context)

elif data == 'send_photo':
await handle_send_photo_callback(query, context)

elif data == 'send_view_once':
await handle_send_view_once_callback(query, context)

# Creative Features - Games
elif data == 'games_menu':
await query.edit_message_text(
  "🎮 **Choose a Game to Play!**\n\nPick a game to play with your chat partner:",
  reply_markup = Keyboards.games_menu(),
  parse_mode = 'Markdown'
)

elif data == 'game_wyr':
question = random.choice(Games.WOULD_YOU_RATHER)
partner_id = matchmaking.get_partner(user_id)
if partner_id:
await query.edit_message_text(f"🤔 **Would You Rather**\n\n {
  question
}", parse_mode = 'Markdown')
await context.bot.send_message(partner_id, f"🤔 **Would You Rather**\n\n {
  question
}", parse_mode = 'Markdown')
else :
await query.answer("❌ You're not in a chat!", show_alert = True)

elif data == 'game_tod':
await query.edit_message_text(
  "🎲 **Truth or Dare**\n\nChoose Truth or Dare:",
  reply_markup = Keyboards.truth_or_dare(),
  parse_mode = 'Markdown'
)

elif data == 'tod_truth':
question = random.choice(Games.TRUTH_OR_DARE['truth'])
partner_id = matchmaking.get_partner(user_id)
if partner_id:
await query.edit_message_text(f"✨ **Truth**\n\n {
  question
}", parse_mode = 'Markdown')
await context.bot.send_message(partner_id, f"✨ **Truth Question for Partner**\n\n {
  question
}", parse_mode = 'Markdown')
else :
await query.answer("❌ You're not in a chat!", show_alert = True)

elif data == 'tod_dare':
dare = random.choice(Games.TRUTH_OR_DARE['dare'])
partner_id = matchmaking.get_partner(user_id)
if partner_id:
await query.edit_message_text(f"🔥 **Dare**\n\n {
  dare
}", parse_mode = 'Markdown')
await context.bot.send_message(partner_id, f"🔥 **Dare for Partner**\n\n {
  dare
}", parse_mode = 'Markdown')
else :
await query.answer("❌ You're not in a chat!", show_alert = True)

elif data == 'game_ttal':
instruction = random.choice(Games.TWO_TRUTHS_LIE)
partner_id = matchmaking.get_partner(user_id)
if partner_id:
await query.edit_message_text(f"🎭 **Two Truths & A Lie**\n\n {
  instruction
}", parse_mode = 'Markdown')
await context.bot.send_message(partner_id, f"🎭 **Two Truths & A Lie**\n\n {
  instruction
}", parse_mode = 'Markdown')
else :
await query.answer("❌ You're not in a chat!", show_alert = True)

# Creative Features - Social
elif data == 'icebreaker':
question = random.choice(IceBreakers.QUESTIONS)
partner_id = matchmaking.get_partner(user_id)
if partner_id:
await query.answer("💡 Icebreaker sent!")
await context.bot.send_message(user_id, f"💡 **Icebreaker Question**\n\n {
  question
}", parse_mode = 'Markdown')
await context.bot.send_message(partner_id, f"💡 **Icebreaker Question**\n\n {
  question
}", parse_mode = 'Markdown')
else :
await query.answer("❌ You're not in a chat!", show_alert = True)

elif data == 'send_compliment':
compliment = random.choice(Compliments.LIST)
partner_id = matchmaking.get_partner(user_id)
if partner_id:
with database.get_db() as db:
user = database.get_user(db, user_id)
if user:
await query.answer("💬 Compliment sent!")
await context.bot.send_message(partner_id, f"💬 ** {
  user.nickname
} sent you a compliment:**\n\n {
  compliment
}", parse_mode = 'Markdown')
else :
await query.answer("❌ You're not in a chat!", show_alert = True)

elif data == 'fun_fact':
fact = random.choice(FunFacts.FACTS)
partner_id = matchmaking.get_partner(user_id)
if partner_id:
await query.answer("🎯 Fun fact sent!")
await context.bot.send_message(user_id, f"🎯 **Fun Fact**\n\n {
  fact
}", parse_mode = 'Markdown')
await context.bot.send_message(partner_id, f"🎯 **Fun Fact**\n\n {
  fact
}", parse_mode = 'Markdown')
else :
await query.answer("❌ You're not in a chat!", show_alert = True)

elif data == 'daily_topic':
topic = random.choice(DailyTopics.TOPICS)
partner_id = matchmaking.get_partner(user_id)
if partner_id:
await query.answer("📅 Topic sent!")
await context.bot.send_message(user_id, f"📅 **Today's Topic**\n\nLet's talk about: {
  topic
}", parse_mode = 'Markdown')
await context.bot.send_message(partner_id, f"📅 **Today's Topic**\n\nLet's talk about: {
  topic
}", parse_mode = 'Markdown')
else :
await query.answer("❌ You're not in a chat!", show_alert = True)

elif data == 'send_gift':
await query.edit_message_text(
  "🎁 **Send a Virtual Gift**\n\nChoose a gift to send to your partner:",
  reply_markup = Keyboards.virtual_gifts(),
  parse_mode = 'Markdown'
)

elif data.startswith('gift_'):
emoji = data.replace('gift_', '')
gift_name = VirtualGifts.GIFTS.get(emoji, 'Gift')
partner_id = matchmaking.get_partner(user_id)
if partner_id:
with database.get_db() as db:
user = database.get_user(db, user_id)
if user:
await query.answer("🎁 Gift sent!")
await context.bot.send_message(
  partner_id,
f"🎁 ** {
    user.nickname
  } sent you a {
    gift_name
  }!** {
    emoji
  }",
  parse_mode = 'Markdown'
)
await query.edit_message_text(
f"✅ You sent a {
  gift_name
} {
  emoji
} to your partner!",
  parse_mode = 'Markdown'
)
else :
await query.answer("❌ You're not in a chat!", show_alert = True)

# Mood System
elif data == 'set_mood':
await query.edit_message_text(
  "😊 **Set Your Mood**\n\nChoose your current mood:",
  reply_markup = Keyboards.mood_selector(),
  parse_mode = 'Markdown'
)

elif data.startswith('mood_'):
emoji = data.replace('mood_', '')
mood_name = Moods.OPTIONS.get(emoji, 'Unknown')
with database.get_db() as db:
user = database.get_user(db, user_id)
if user:
user.mood = emoji
db.commit()
await query.answer(f"Mood set to {
  mood_name
} {
  emoji
}!")
await query.edit_message_text(
f"✅ **Mood Updated!**\n\nYour mood is now: {
  mood_name
} {
  emoji
}",
  reply_markup = Keyboards.profile_menu(),
  parse_mode = 'Markdown'
)

# Language Selection
elif data == 'change_language':
await query.edit_message_text(
  get_text('LANG_SELECT', 'en'),
  reply_markup = Keyboards.language_selection(),
  parse_mode = 'Markdown'
)

elif data.startswith('lang_'):
lang_code = data.replace('lang_', '')
with database.get_db() as db:
database.update_user_profile(db, user_id, 'language', lang_code)
db.commit()
await query.answer(get_text('LANG_CHANGED', lang_code))
await query.edit_message_text(
  get_text('LANG_CHANGED', lang_code),
  reply_markup = Keyboards.profile_menu(),
  parse_mode = 'Markdown'
)

# Search controls
elif data == 'stop_search':
await handle_stop_search_callback(query, context)

elif data == 'refresh_search':
await handle_refresh_search_callback(query, context)

# Admin panel
elif data.startswith('admin_') and is_admin(user_id):
await handle_admin_callback(query, context)

async def handle_gender_selection(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle gender selection during registration"""
user_id = query.from_user.id
telegram_user = query.from_user
gender = query.data.replace('gender_', '')

with database.get_db() as db:
# Check if user already exists
existing_user = database.get_user(db, user_id)
if existing_user:
await query.edit_message_text(
f"👋 Welcome back, ** {
  existing_user.nickname
}**!",
  reply_markup = Keyboards.main_menu(),
  parse_mode = 'Markdown'
)
return

# Create new user
nickname = get_unique_nickname()
user = database.create_user(
  db, user_id,
  telegram_user.username or "",
  telegram_user.first_name or "",
  telegram_user.last_name or "",
  gender, nickname
)

await query.edit_message_text(
  Messages.GENDER_SET.format(nickname, gender.title()),
  reply_markup = Keyboards.main_menu(),
  parse_mode = 'Markdown'
)

# Button Callback Functions
async def handle_find_partner_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle find partner button callback"""
user_id = query.from_user.id

with database.get_db() as db:
user = database.get_user(db, user_id)
if not user:
await query.edit_message_text("❌ Please register first using /start")
return

if user.is_banned:
await query.edit_message_text("❌ Your account is suspended.")
return

if matchmaking.get_partner(user_id):
await query.edit_message_text(Messages.ALREADY_IN_CHAT, reply_markup = Keyboards.chat_controls())
return

if user_id in matchmaking.waiting_users:
await query.edit_message_text(Messages.ALREADY_WAITING)
return

if await matchmaking.add_to_queue(user_id):
# Try to find partner immediately
partner_id = await matchmaking.find_partner(user_id, context)
if partner_id:
# Store message info for auto-deletion and notify match
context.user_data[f'search_message_ {
  user_id
}'] = {
  'chat_id': query.message.chat_id, 'message_id': query.message.message_id
}
await matchmaking.notify_match(context, user_id, partner_id)
else :
await query.edit_message_text(
  Messages.MATCHING_STARTED,
  reply_markup = Keyboards.searching_controls()
)
# Store message info for potential auto-deletion later
context.user_data[f'search_message_ {
  user_id
}'] = {
  'chat_id': query.message.chat_id, 'message_id': query.message.message_id
} else :
await query.edit_message_text("❌ Unable to start matching. Please try again.")

async def show_profile_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle view profile button callback"""
user_id = query.from_user.id

with database.get_db() as db:
user = database.get_user(db, user_id)
if not user:
await query.edit_message_text("❌ Please register first using /start")
return

interests = ", ".join([interest.name for interest in user.interests]) if user.interests else "None set"
created_date = user.created_at.strftime("%B %d, %Y")
mood_display = f" {
  user.mood
} {
  Moods.OPTIONS.get(user.mood, '')}" if user.mood else "Not set"

profile_text = Messages.PROFILE_INFO.format(
  user.nickname,
  user.gender.title(),
  mood_display,
  user.bio or "Not set",
  user.age or "Not set",
  user.location or "Not set",
  interests,
  user.total_chats,
  created_date
)

await query.edit_message_text(
  profile_text,
  reply_markup = Keyboards.profile_menu(),
  parse_mode = 'Markdown'
)


# Profile Management Handlers
async def handle_edit_profile_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle edit profile button callback"""
edit_menu = InlineKeyboardMarkup([
  [InlineKeyboardButton("🎭 Change Nickname", callback_data = 'edit_nickname')],
  [InlineKeyboardButton("👤 Change Gender", callback_data = 'edit_gender')],
  [InlineKeyboardButton("📝 Edit Bio", callback_data = 'edit_bio')],
  [InlineKeyboardButton("🎂 Edit Age", callback_data = 'edit_age')],
  [InlineKeyboardButton("📍 Edit Location", callback_data = 'edit_location')],
  [InlineKeyboardButton("🔙 Back to Profile", callback_data = 'view_profile')],
  [InlineKeyboardButton("🏠 Main Menu", callback_data = 'main_menu')]
])

await query.edit_message_text(
  "✏️ **Edit Profile**\n\nWhat would you like to edit?",
  reply_markup = edit_menu,
  parse_mode = 'Markdown'
)

async def handle_set_interests_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle set interests button callback"""
await query.edit_message_text(
  "💭 **Set Your Interests**\n\nType your interests separated by commas (e.g., music, sports, movies):",
  parse_mode = 'Markdown'
)
context.user_data['editing_state'] = 'interests'

async def handle_profile_edit_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle specific profile field editing"""
data = query.data

if data == 'edit_bio':
await query.edit_message_text(
  "📝 **Edit Bio**\n\nTell us about yourself (max 200 characters):",
  parse_mode = 'Markdown'
)
context.user_data['editing_state'] = 'bio'

elif data == 'edit_age':
await query.edit_message_text(
  "🎂 **Edit Age**\n\nEnter your age (18-80):",
  parse_mode = 'Markdown'
)
context.user_data['editing_state'] = 'age'

elif data == 'edit_location':
await query.edit_message_text(
  "📍 **Edit Location**\n\nEnter your location (city, country):",
  parse_mode = 'Markdown'
)
context.user_data['editing_state'] = 'location'

elif data == 'edit_nickname':
await query.edit_message_text(
  "🎭 **Change Nickname**\n\nEnter your new nickname (2-20 characters):",
  parse_mode = 'Markdown'
)
context.user_data['editing_state'] = 'nickname'

elif data == 'edit_gender':
gender_menu = InlineKeyboardMarkup([
  [InlineKeyboardButton("👨 Male", callback_data = 'change_gender_male')],
  [InlineKeyboardButton("👩 Female", callback_data = 'change_gender_female')],
  [InlineKeyboardButton("🔙 Back", callback_data = 'edit_profile')]
])
await query.edit_message_text(
  "👤 **Change Gender**\n\nSelect your gender:",
  reply_markup = gender_menu,
  parse_mode = 'Markdown'
)

async def handle_change_gender_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle gender change callback"""
user_id = query.from_user.id
gender = query.data.replace('change_gender_', '')

with database.get_db() as db:
success = database.update_user_profile(db, user_id, 'gender', gender)
if success:
db.commit()
await query.edit_message_text(
f"✅ Gender updated to ** {
  gender.title()}**!",
  reply_markup = Keyboards.profile_menu(),
  parse_mode = 'Markdown'
)
else :
await query.edit_message_text(
  "❌ Failed to update gender. Please try again.",
  reply_markup = Keyboards.profile_menu()
)

async def handle_view_partner_profile_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle view partner profile during chat"""
user_id = query.from_user.id
partner_id = matchmaking.get_partner(user_id)

if not partner_id:
await query.answer("❌ You're not in a chat right now.")
return

with database.get_db() as db:
partner = database.get_user(db, partner_id)
if not partner:
await query.answer("❌ Partner not found.")
return

interests = ", ".join([interest.name for interest in partner.interests]) if partner.interests else "None set"

profile_text = f"""👤 **Partner's Profile**

🎭 **Nickname:** {
  partner.nickname
}
👤 **Gender:** {
  partner.gender.title()}
📝 **Bio:** {
  partner.bio or "Not set"
}
🎂 **Age:** {
  partner.age or "Not set"
}
📍 **Location:** {
  partner.location or "Not set"
}
💭 **Interests:** {
  interests
}"""

back_to_chat = InlineKeyboardMarkup([
  [InlineKeyboardButton("🔙 Back to Chat", callback_data = 'back_to_chat')],
  [InlineKeyboardButton("🏠 Main Menu", callback_data = 'main_menu')]
])

await query.edit_message_text(
  profile_text,
  reply_markup = back_to_chat,
  parse_mode = 'Markdown'
)

async def handle_send_photo_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle send photo option during chat"""
user_id = query.from_user.id
partner_id = matchmaking.get_partner(user_id)

if not partner_id:
await query.answer("❌ You're not in a chat right now.")
return

await query.edit_message_text(
  "📷 **Send a Photo**\n\nSend one photo now. Your partner will receive it (protected from screenshots):",
  parse_mode = 'Markdown'
)
context.user_data['sending_photo'] = True
context.user_data['photo_partner'] = partner_id

async def handle_send_view_once_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle send view-once photo option during chat"""
user_id = query.from_user.id
partner_id = matchmaking.get_partner(user_id)

if not partner_id:
await query.answer("❌ You're not in a chat right now.")
return

await query.edit_message_text(
  "💥 **Send View-Once Photo**\n\nSend one photo now. Your partner will see it only once and it will disappear after viewing:",
  parse_mode = 'Markdown'
)
context.user_data['sending_view_once'] = True
context.user_data['photo_partner'] = partner_id

async def handle_skip_chat_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle skip chat button callback"""
user_id = query.from_user.id
partner_id = await matchmaking.end_chat(user_id)

if partner_id:
await query.edit_message_text(Messages.SKIPPED_CHAT)
await context.bot.send_message(partner_id, Messages.PARTNER_SKIPPED, reply_markup = Keyboards.main_menu())

# Start new search for current user - Add them back to queue
if await matchmaking.add_to_queue(user_id):
await context.bot.send_message(user_id, Messages.MATCHING_STARTED)
task = asyncio.create_task(matchmaking.start_matching_with_retry(user_id, context))
matchmaking.retry_tasks[user_id] = task
else :
await query.edit_message_text(Messages.NOT_IN_CHAT, reply_markup = Keyboards.main_menu())

async def handle_end_chat_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle end chat button callback"""
user_id = query.from_user.id
partner_id = await matchmaking.end_chat(user_id)
await matchmaking.remove_from_queue(user_id)

if partner_id:
await query.edit_message_text(Messages.CHAT_ENDED, reply_markup = Keyboards.main_menu())
await context.bot.send_message(partner_id, Messages.CHAT_ENDED_BY_PARTNER, reply_markup = Keyboards.main_menu())
else :
await query.edit_message_text(Messages.CHAT_ENDED, reply_markup = Keyboards.main_menu())

async def handle_report_user_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle report user button callback"""
user_id = query.from_user.id
partner_id = matchmaking.get_partner(user_id)

if not partner_id:
await query.edit_message_text(Messages.REPORT_ONLY_IN_CHAT)
return

with database.get_db() as db:
session = database.get_active_chat_session(db, user_id)
database.create_user_report(
  db, user_id, partner_id,
  session.id if session else None,
  "Reported via bot command"
)

# End the chat
await matchmaking.end_chat(user_id)
await query.edit_message_text(Messages.REPORT_SENT, reply_markup = Keyboards.main_menu())

if partner_id:
await context.bot.send_message(partner_id, Messages.CHAT_ENDED_BY_PARTNER, reply_markup = Keyboards.main_menu())

# Admin Functions
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle /admin command"""
user_id = update.effective_user.id

if not is_admin(user_id):
await update.message.reply_text("❌ Access denied.")
return

await update.message.reply_text(
  Messages.ADMIN_PANEL,
  reply_markup = Keyboards.admin_panel(),
  parse_mode = 'Markdown'
)

async def handle_admin_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle admin panel callbacks"""
data = query.data

if data == 'admin_broadcast':
cancel_keyboard = InlineKeyboardMarkup([
  [InlineKeyboardButton("❌ Cancel Broadcast", callback_data = 'admin_broadcast_cancel')]
])
await query.edit_message_text(
  "📢 **Broadcast Message**\n\nSend your message now. It will be sent to all users:",
  reply_markup = cancel_keyboard,
  parse_mode = 'Markdown'
)
context.user_data['admin_state'] = 'awaiting_broadcast'

elif data == 'admin_broadcast_cancel':
context.user_data.pop('admin_state', None)
await query.edit_message_text(
  "❌ Broadcast cancelled.",
  reply_markup = Keyboards.admin_panel(),
  parse_mode = 'Markdown'
)

elif data == 'admin_stats':
with database.get_db() as db:
total_users = db.query(database.User).count()
active_users = database.get_active_users_count(db)
active_chats = len(matchmaking.active_sessions) // 2
waiting_users = len(matchmaking.waiting_users)

stats_text = f"""📊 **Bot Statistics**
👥 **Total Users:** {
  total_users
}
🟢 **Active Today:** {
  active_users
}
💬 **Active Chats:** {
  active_chats
}
⏳ **Waiting Queue:** {
  waiting_users
}
📅 **Date:** {
  datetime.now().strftime('%Y-%m-%d %H:%M')}"""

await query.edit_message_text(stats_text, parse_mode = 'Markdown')

elif data == 'admin_users':
user_mgmt_menu = InlineKeyboardMarkup([
  [InlineKeyboardButton("🚫 Ban User", callback_data = 'admin_ban_user')],
  [InlineKeyboardButton("✅ Unban User", callback_data = 'admin_unban_user')],
  [InlineKeyboardButton("📋 List Banned", callback_data = 'admin_list_banned')],
  [InlineKeyboardButton("🔙 Back", callback_data = 'admin_panel_back')]
])
await query.edit_message_text(
  "👥 **User Management**\n\nChoose an action:",
  reply_markup = user_mgmt_menu,
  parse_mode = 'Markdown'
)

elif data == 'admin_reports':
with database.get_db() as db:
reports = database.get_pending_reports(db)
if not reports:
await query.edit_message_text(
  "📝 **Reports**\n\n✅ No pending reports.",
  parse_mode = 'Markdown'
)
return

reports_text = "📝 **Pending Reports**\n\n"
for report in reports[:10]: # Show max 10 reports
reporter = database.get_user(db, report.reporter_id)
reported = database.get_user(db, report.reported_id)
reports_text += f"**Report # {
  report.id
}**\n"
reports_text += f"👤 Reporter: {
  reporter.nickname if reporter else 'Unknown'
} (ID: {
  report.reporter_id
})\n"
reports_text += f"🎯 Reported: {
  reported.nickname if reported else 'Unknown'
} (ID: {
  report.reported_id
})\n"
reports_text += f"📝 Reason: {
  report.reason or 'No reason provided'
}\n"
reports_text += f"📅 Date: {
  report.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"

if len(reports) > 10:
reports_text += f"... and {
  len(reports) - 10
} more reports"

await query.edit_message_text(reports_text, parse_mode = 'Markdown')

elif data == 'admin_ban_user':
await query.edit_message_text(
  "🚫 **Ban User**\n\nSend the user ID to ban:",
  parse_mode = 'Markdown'
)
context.user_data['admin_state'] = 'awaiting_ban_user'

elif data == 'admin_unban_user':
await query.edit_message_text(
  "✅ **Unban User**\n\nSend the user ID to unban:",
  parse_mode = 'Markdown'
)
context.user_data['admin_state'] = 'awaiting_unban_user'

elif data == 'admin_list_banned':
with database.get_db() as db:
banned_users = database.get_banned_users(db)
if not banned_users:
await query.edit_message_text(
  "📋 **Banned Users**\n\n✅ No banned users.",
  parse_mode = 'Markdown'
)
return

banned_text = "📋 **Banned Users**\n\n"
for user in banned_users[:15]: # Show max 15
banned_text += f"** {
  user.nickname
}** (ID: {
  user.user_id
})\n"
banned_text += f"📝 Reason: {
  user.ban_reason or 'No reason'
}\n"
banned_text += f"📅 Banned: {
  user.ban_date.strftime('%Y-%m-%d')}\n\n"

if len(banned_users) > 15:
banned_text += f"... and {
  len(banned_users) - 15
} more"

await query.edit_message_text(banned_text, parse_mode = 'Markdown')

elif data == 'admin_panel_back':
await query.edit_message_text(
  Messages.ADMIN_PANEL,
  reply_markup = Keyboards.admin_panel(),
  parse_mode = 'Markdown'
)

# Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle all text messages"""
# Safety check for message
if not update.message or not update.message.text:
return

user_id = update.effective_user.id
message_text = update.message.text

# Check for admin states
admin_state = context.user_data.get('admin_state')
if admin_state and is_admin(user_id):
if admin_state == 'awaiting_broadcast':
await handle_admin_broadcast(update, context)
return
elif admin_state == 'awaiting_ban_user':
await handle_admin_ban_user(update, context)
return
elif admin_state == 'awaiting_unban_user':
await handle_admin_unban_user(update, context)
return
elif admin_state == 'awaiting_ban_reason':
await handle_admin_ban_reason(update, context)
return

# Check for profile editing states
editing_state = context.user_data.get('editing_state')
if editing_state:
await handle_profile_editing(update, context, editing_state)
return

# Check if user is searching - block commands during search
if user_id in matchmaking.waiting_users:
await update.message.reply_text(
  "🔍 You're currently searching for a partner. Please use the search control buttons or stop your search to use commands."
)
return

# Check if user is in chat
partner_id = matchmaking.get_partner(user_id)

if partner_id:
# Forward message to partner with content warning if needed
if contains_inappropriate_content(message_text):
await update.message.reply_text(Messages.WARNING_MESSAGE, parse_mode = 'Markdown')

try:
await context.bot.send_message(
  partner_id,
  message_text,
  protect_content = True # Prevent screenshots and forwarding
)

# Update activity
with database.get_db() as db:
database.update_user_activity(db, user_id)

except TelegramError as e:
logger.error(f"Failed to forward message: {
  e
}")
await update.message.reply_text("❌ Failed to send message. Your partner may have left.")
else :
# User not in chat - show main menu
with database.get_db() as db:
user = database.get_user(db, user_id)
if user:
await update.message.reply_text(
  "💬 You're not in a chat right now. Use the menu to find a partner:",
  reply_markup = Keyboards.main_menu()
)
else :
await update.message.reply_text("❌ Please register first using /start")

async def handle_admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle admin broadcast message"""

message = update.message.text
admin_id = update.effective_user.id

with database.get_db() as db:
# Create broadcast record i5
broadcast = database.create_broadcast_message(db, admin_id, message)
user_ids = database.get_all_user_ids(db)

await update.message.reply_text(f"📢 Broadcasting to {
  len(user_ids)} users...")

sent_count = 0
failed_count = 0

for user_id in user_ids:
try:
await context.bot.send_message(
  user_id,
f"📢 **Admin Announcement**\n\n {
    message
  }",
  parse_mode = 'Markdown'
)
sent_count += 1
except TelegramError:
failed_count += 1

# Update broadcast statistics
with database.get_db() as db:
database.update_broadcast_stats(db, broadcast.id, sent_count, failed_count)

await update.message.reply_text(
f"✅ **Broadcast Complete**\n\n📤 Sent: {
  sent_count
}\n❌ Failed: {
  failed_count
}",
  reply_markup = Keyboards.admin_panel(),
  parse_mode = 'Markdown'
)

context.user_data.pop('admin_state', None)

# New handler functions for admin and profile management
async def handle_admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle admin ban user"""
try:
user_id_to_ban = int(update.message.text.strip())
admin_id = update.effective_user.id

with database.get_db() as db:
user = database.get_user(db, user_id_to_ban)
if not user:
await update.message.reply_text("❌ User not found.")
return

if user.is_banned:
await update.message.reply_text(f"⚠️ User {
  user.nickname
} (ID: {
  user_id_to_ban
}) is already banned.")
return

# Ask for ban reason
context.user_data['ban_user_id'] = user_id_to_ban
context.user_data['admin_state'] = 'awaiting_ban_reason'
await update.message.reply_text(
f"👤 ** {
  user.nickname
}** (ID: {
  user_id_to_ban
})\n\nEnter ban reason (or send 'skip' for no reason):",
  parse_mode = 'Markdown'
)

except ValueError:
await update.message.reply_text("❌ Please send a valid user ID number.")
except Exception as e:
await update.message.reply_text(f"❌ Error: {
  str(e)}")

async def handle_admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle admin unban user"""
try:
user_id_to_unban = int(update.message.text.strip())
admin_id = update.effective_user.id

with database.get_db() as db:
user = database.get_user(db, user_id_to_unban)
if not user:
await update.message.reply_text("❌ User not found.")
return

if not user.is_banned:
await update.message.reply_text(f"⚠️ User {
  user.nickname
} (ID: {
  user_id_to_unban
}) is not banned.")
return

database.unban_user(db, user_id_to_unban, admin_id)
db.commit()

await update.message.reply_text(
f"✅ **User Unbanned**\n\n👤 {
  user.nickname
} (ID: {
  user_id_to_unban
}) has been unbanned.",
  parse_mode = 'Markdown'
)

except ValueError:
await update.message.reply_text("❌ Please send a valid user ID number.")
except Exception as e:
await update.message.reply_text(f"❌ Error: {
  str(e)}")

context.user_data.pop('admin_state', None)

async def handle_profile_editing(update: Update, context: ContextTypes.DEFAULT_TYPE, editing_state: str) -> None:
"""Handle profile editing states"""
user_id = update.effective_user.id
message_text = update.message.text

with database.get_db() as db:
success = False

if editing_state == 'bio':
if len(message_text) <= 200:
success = database.update_user_profile(db, user_id, 'bio', message_text)
else :
await update.message.reply_text("❌ Bio must be 200 characters or less. Try again:")
return

elif editing_state == 'age':
success = database.update_user_profile(db, user_id, 'age', message_text)
if not success:
await update.message.reply_text("❌ Please enter a valid age between 18 and 80:")
return

elif editing_state == 'location':
if len(message_text) <= 100:
success = database.update_user_profile(db, user_id, 'location', message_text)
else :
await update.message.reply_text("❌ Location must be 100 characters or less. Try again:")
return

elif editing_state == 'interests':
interests = [i.strip() for i in message_text.split(',') if i.strip()]
if len(interests) > 10:
await update.message.reply_text("❌ Maximum 10 interests allowed. Try again:")
return
success = database.set_user_interests(db, user_id, interests)

elif editing_state == 'nickname':
if len(message_text) < 2 or len(message_text) > 20:
await update.message.reply_text("❌ Nickname must be 2-20 characters. Try again:")
return
success = database.update_user_profile(db, user_id, 'nickname', message_text)
if not success:
await update.message.reply_text("❌ This nickname is already taken or invalid. Try a different one:")
return

if success:
db.commit()
await update.message.reply_text(
  "✅ Profile updated successfully!",
  reply_markup = Keyboards.profile_menu()
)
else :
await update.message.reply_text("❌ Failed to update profile. Please try again.")

context.user_data.pop('editing_state', None)

# Photo handler
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle photo messages"""
# Safety check for message
if not update.message:
return

user_id = update.effective_user.id

# Check if user is sending a view-once photo
if context.user_data.get('sending_view_once'):
partner_id = context.user_data.get('photo_partner')

if partner_id and matchmaking.get_partner(user_id) == partner_id:
try:
# Send view-once photo to partner with auto-delete functionality
sent_message = await context.bot.send_photo(
  partner_id,
  update.message.photo[-1].file_id,
  caption = "💥 Your chat partner sent you a view-once photo! This will be deleted after 30 seconds.",
  protect_content = True,
  has_spoiler = True # Makes photo blurred until clicked
)

# Schedule deletion of the view-once photo after 30 seconds
async def delete_view_once_photo():
await asyncio.sleep(30)
try:
await context.bot.delete_message(chat_id = partner_id, message_id = sent_message.message_id)
except Exception as e:
logger.debug(f"Failed to delete view-once photo: {
  e
}")

asyncio.create_task(delete_view_once_photo())

await update.message.reply_text(
  "✅ View-once photo sent! It will disappear after your partner views it.",
  reply_markup = Keyboards.chat_controls()
)

except TelegramError as e:
logger.error(f"Failed to forward view-once photo: {
  e
}")
await update.message.reply_text("❌ Failed to send photo. Your partner may have left.")
else :
await update.message.reply_text("❌ You're not in an active chat.")

context.user_data.pop('sending_view_once', None)
context.user_data.pop('photo_partner', None)

# Check if user is sending a regular photo in chat
elif context.user_data.get('sending_photo'):
partner_id = context.user_data.get('photo_partner')

if partner_id and matchmaking.get_partner(user_id) == partner_id:
try:
# Forward protected photo to partner
await context.bot.send_photo(
  partner_id,
  update.message.photo[-1].file_id,
  caption = "📷 Your chat partner sent you a photo!",
  protect_content = True # Prevent screenshots and forwarding
)

await update.message.reply_text(
  "✅ Photo sent to your partner! (Protected from screenshots)",
  reply_markup = Keyboards.chat_controls()
)

except TelegramError as e:
logger.error(f"Failed to forward photo: {
  e
}")
await update.message.reply_text("❌ Failed to send photo. Your partner may have left.")
else :
await update.message.reply_text("❌ You're not in an active chat.")

context.user_data.pop('sending_photo', None)
context.user_data.pop('photo_partner', None)

else :
# Check if user is in an active chat and allow normal photo sending
partner_id = matchmaking.get_partner(user_id)
if partner_id:
try:
# Send normal photo to partner
await context.bot.send_photo(
  partner_id,
  update.message.photo[-1].file_id,
  caption = "📷 Your chat partner sent you a photo!",
  protect_content = True # Prevent screenshots and forwarding
)

await update.message.reply_text(
  "✅ Photo sent to your partner! (Protected from screenshots)",
  reply_markup = Keyboards.chat_controls()
)

except TelegramError as e:
logger.error(f"Failed to forward photo: {
  e
}")
await update.message.reply_text("❌ Failed to send photo. Your partner may have left.")
else :
# User sent photo outside of chat
await update.message.reply_text(
  "📷 To send photos, you need to be in an active chat.",
  reply_markup = Keyboards.main_menu()
)

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle sticker messages"""
if not update.message or not update.message.sticker:
return

user_id = update.effective_user.id

partner_id = matchmaking.get_partner(user_id)
if partner_id:
try:
await context.bot.send_sticker(
  partner_id,
  update.message.sticker.file_id,
  protect_content = True
)
except TelegramError as e:
logger.error(f"Failed to forward sticker: {
  e
}")
await update.message.reply_text("❌ Failed to send sticker. Your partner may have left.")
else :
await update.message.reply_text(
  "🎨 To send stickers, you need to be in an active chat.",
  reply_markup = Keyboards.main_menu()
)

async def handle_admin_ban_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle admin ban reason input"""
reason = update.message.text.strip()
user_id_to_ban = context.user_data.get('ban_user_id')
admin_id = update.effective_user.id

if not user_id_to_ban:
await update.message.reply_text("❌ Session expired. Please try again.")
context.user_data.pop('admin_state', None)
return

ban_reason = None if reason.lower() == 'skip' else reason

try:
with database.get_db() as db:
user = database.get_user(db, user_id_to_ban)
if not user:
await update.message.reply_text("❌ User not found.")
return

database.ban_user(db, user_id_to_ban, admin_id, ban_reason)
db.commit()

# Remove user from any active chat
partner_id = matchmaking.get_partner(user_id_to_ban)
if partner_id:
matchmaking.end_session(user_id_to_ban, partner_id)

await update.message.reply_text(
f"⛔ **User Banned**\n\n👤 {
  user.nickname
} (ID: {
  user_id_to_ban
})\n📝 Reason: {
  ban_reason or 'No reason provided'
}",
  parse_mode = 'Markdown'
)

except Exception as e:
await update.message.reply_text(f"❌ Error: {
  str(e)}")

context.user_data.pop('admin_state', None)
context.user_data.pop('ban_user_id', None)

async def viewonce_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle /viewonce command for sending disappearing photos"""
user_id = update.effective_user.id
partner_id = matchmaking.get_partner(user_id)

if not partner_id:
await update.message.reply_text(
  "❌ You need to be in an active chat to send view-once photos. Use /find to start chatting!",
  reply_markup = Keyboards.main_menu()
)
return

await update.message.reply_text(
  "💥 **Send View-Once Photo**\n\nSend one photo now. Your partner will see it only once and it will disappear after 30 seconds:",
  parse_mode = 'Markdown'
)
context.user_data['sending_view_once'] = True
context.user_data['photo_partner'] = partner_id

# Search control handlers
async def handle_stop_search_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle stop search button callback"""
user_id = query.from_user.id

# Remove user from waiting queue
await matchmaking.remove_from_queue(user_id)

# Cancel any retry task
if user_id in matchmaking.retry_tasks:
task = matchmaking.retry_tasks[user_id]
if not task.done():
task.cancel()
del matchmaking.retry_tasks[user_id]

await query.edit_message_text(
  Messages.SEARCH_STOPPED,
  reply_markup = Keyboards.main_menu(),
  parse_mode = 'Markdown'
)

async def handle_refresh_search_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Handle refresh search button callback"""
user_id = query.from_user.id

# Check if user is still in waiting queue
if user_id not in matchmaking.waiting_users:
await query.edit_message_text(
  "❌ You're not currently searching. Use the menu to start a new search:",
  reply_markup = Keyboards.main_menu()
)
return
async def saved_chats_command(update, context):

user_id = update.effective_user.id
saved = database.get_saved_chats(user_id)

if not saved:
await update.message.reply_text("📂 No saved chats.")
return

keyboard = []

for row in saved:
sid = row["saved_user_id"]

keyboard.append([
  InlineKeyboardButton("🔄 Reconnect", callback_data = f"reconnect_ {
    sid
  }"),
  InlineKeyboardButton("❌ Remove", callback_data = f"remove_saved_ {
    sid
  }")
])

await update.message.reply_text(
  "📂 Saved Chats:",
  reply_markup = InlineKeyboardMarkup(keyboard)
)
# Try to find a partner
partner_id = await matchmaking.find_partner(user_id, context)
if partner_id:
await matchmaking.notify_match(context, user_id, partner_id)
else :
await query.edit_message_text(
  Messages.NO_PARTNER_FOUND,
  reply_markup = Keyboards.searching_controls(),
  parse_mode = 'Markdown'
)

def main() -> None:
"""Start the bot"""
# Initialize database
database.init_database()

# Create application
application = Application.builder().token(TOKEN).build()

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("find", find_partner_command))
application.add_handler(CommandHandler("saved", saved_chats_command))
application.add_handler(CommandHandler("skip", skip_command))
application.add_handler(CommandHandler("stop", stop_command))
application.add_handler(CommandHandler("report", report_command))
application.add_handler(CommandHandler("profile", profile_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("privacy", privacy_command))
application.add_handler(CommandHandler("viewonce", viewonce_command))
application.add_handler(CommandHandler("admin", admin_command))

application.add_handler(CallbackQueryHandler(button_callback))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, block_personal_info),group = 0)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),group = 1)

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Set bot commands
async def set_commands():
commands = [
  BotCommand("start", "Start the bot and register"),
  BotCommand("saved", "View saved chat list"),
  BotCommand("find", "Find a chat partner"),
  BotCommand("skip", "Skip current chat partner"),
  BotCommand("stop", "End current chat"),
  BotCommand("profile", "View/edit your profile"),
  BotCommand("viewonce", "Send a view-once disappearing photo"),
  BotCommand("help", "Show help menu"),
  BotCommand("privacy", "Privacy information"),
  BotCommand("admin", "Admin panel (admin only)")
]
await application.bot.set_my_commands(commands)

# Set commands when bot starts
async def startup():
await set_commands()

if application.job_queue:
application.job_queue.run_once(lambda context: asyncio.create_task(startup()), 0)
else :
# If no job queue, set commands directly when starting
async def post_init(application):
await startup()
application.post_init = post_init

# Add error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
"""Log errors caused by updates."""
logger.error(f"Exception while handling an update: {
  context.error
}")

application.add_error_handler(error_handler)

# Start polling (drop pending updates to avoid conflicts with other instances)
logger.info("Bot started successfully")
application.run_polling(allowed_updates = Update.ALL_TYPES, drop_pending_updates = True)

if __name__ == '__main__':
main()