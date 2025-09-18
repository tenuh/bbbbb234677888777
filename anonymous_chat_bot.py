import logging
import os
import asyncio
import time
import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Union
from datetime import datetime, timedelta

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    InlineQueryResultArticle, 
    InputTextMessageContent,
    Message
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    InlineQueryHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get token from environment (fallback for development - remove for production)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8436060773:AAE2_ofNTrMKokeoc4w48afDdq9AmQjnnRA')
if TOKEN == '8436060773:AAE2_ofNTrMKokeoc4w48afDdq9AmQjnnRA':
    logger.warning("⚠️ Using development token fallback. Set TELEGRAM_BOT_TOKEN environment variable for production!")

# English Constants
class Messages:
    WELCOME = "🎭 Welcome to Anonymous Chat Bot!\n\nConnect with random people around the world anonymously. Choose your preference to get started:"
    HELP = """🔥 **Anonymous Chat Bot Commands**

🎭 **Chat Commands:**
/start - Start the bot and begin matching
/find - Find a random chat partner  
/next - Skip current chat and find someone new
/stop - End current chat session
/report - Report inappropriate behavior

⚙️ **Settings:**
/interests - Set your interests for better matching
/profile - View your profile information
/settings - Change your preferences

📊 **Info:**
/help - Show this help message
/stats - Bot statistics

Use inline mode by typing @botusername in any chat to share the bot with friends!
"""
    
    ALREADY_IN_CHAT = "You're already in a chat session! Use /next to find someone new or /stop to end the chat."
    ALREADY_WAITING = "You're already in the queue, waiting for a chat partner..."
    CHOOSE_GENDER = "Choose your gender preference:"
    MALE = "👨 Male"
    FEMALE = "👩 Female" 
    ANY_GENDER = "🌟 Any Gender"
    
    GENDER_SET = "Thanks! Your nickname is **{}**. You can set interests with /interests for better matching.\n\nSearching for a chat partner..."
    ALREADY_SET = "You've already set your preferences. Use /next to find someone new or /stop to end current chat."
    
    CHAT_ENDED = "Chat session ended. Send /start to begin a new chat!"
    CHAT_ENDED_BY_PARTNER = "Your chat partner ended the session."
    NOT_IN_CHAT = "You're not in a chat session. Send /start to begin chatting!"
    
    SKIPPED_CHAT = "You've skipped this chat. Finding someone new..."
    PARTNER_SKIPPED = "Your chat partner skipped to find someone new. Finding you a new partner..."
    
    REPORT_SENT = "Report submitted. We'll review this conversation. The chat session has been ended."
    REPORT_ONLY_IN_CHAT = "You can only report users while in an active chat session."
    
    NO_PARTNER_AVAILABLE = "No chat partners available right now. You're in the queue - we'll notify you when someone joins!"
    PARTNER_FOUND = "🎉 Connected with **{}**! Start chatting now."
    COMMON_INTERESTS = "\n💫 You both share these interests: {}"
    
    FORBIDDEN_MESSAGE = "Your message contains inappropriate content and won't be sent. Please use respectful language."
    PARTNER_NOT_FOUND = "Chat partner not found. Send /stop to end the session."
    NOT_CONNECTED = "You're not connected to anyone. Send /start to begin a new chat!"
    
    INTERESTS_HELP = "Add your interests to get better matches. Example: /interests movies, music, sports"
    INTERESTS_SET = "Your interests have been saved: {}"
    NEED_GENDER_FIRST = "Please choose your gender first with /start."
    
    PROFILE_INFO = """👤 **Your Profile**
🎭 Nickname: {}
👥 Gender Preference: {}
💭 Interests: {}
📊 Total Chats: {}
⏰ Member Since: {}
"""
    
    INLINE_FIND_TITLE = "🎭 Find Random Chat Partner"
    INLINE_FIND_DESC = "Connect with someone new anonymously"
    INLINE_INVITE_TITLE = "💬 Share Anonymous Chat Invite"  
    INLINE_INVITE_DESC = "Invite friends to chat with you anonymously"
    INLINE_HELP_TITLE = "ℹ️ How Anonymous Chat Works"
    INLINE_HELP_DESC = "Learn about anonymous chatting features"

# Profanity filter - English focused
FORBIDDEN_WORDS = [
    'fuck', 'shit', 'bitch', 'asshole', 'damn', 'hell', 'crap', 'piss', 'dick', 'cock', 
    'pussy', 'cunt', 'whore', 'slut', 'bastard', 'nigger', 'faggot', 'retard', 'gay',
    'kill yourself', 'kys', 'suicide', 'rape', 'nazi', 'hitler'
]

# English nicknames
NICKNAMES = [
    'Phoenix', 'Shadow', 'Storm', 'Raven', 'Wolf', 'Tiger', 'Lion', 'Eagle', 'Bear', 'Fox',
    'Cosmic', 'Nova', 'Star', 'Moon', 'Sun', 'Ocean', 'River', 'Mountain', 'Forest', 'Sky',
    'Crimson', 'Azure', 'Golden', 'Silver', 'Emerald', 'Ruby', 'Sapphire', 'Diamond', 'Pearl', 'Jade',
    'Thunder', 'Lightning', 'Blaze', 'Frost', 'Wind', 'Rain', 'Snow', 'Cloud', 'Mist', 'Dawn',
    'Mystic', 'Sage', 'Dream', 'Vision', 'Spirit', 'Soul', 'Heart', 'Mind', 'Zen', 'Peace'
]

@dataclass
class UserState:
    user_id: int
    own_gender: str  # User's actual gender: 'male' or 'female'
    partner_preference: str  # What they're looking for: 'male', 'female', or 'any'
    nickname: str
    interests: Set[str] = field(default_factory=set)
    total_chats: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    reported_count: int = 0
    is_banned: bool = False

@dataclass
class ChatSession:
    user_a: int
    user_b: int
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

class MatchmakingService:
    def __init__(self):
        self.user_states: Dict[int, UserState] = {}
        self.waiting_users: List[int] = []  # Single queue for all users
        self.active_sessions: Dict[int, ChatSession] = {}
        self.lock = asyncio.Lock()
        self.user_last_action: Dict[int, float] = {}
        
    async def create_user(self, user_id: int, own_gender: str, partner_preference: str) -> UserState:
        async with self.lock:
            if user_id in self.user_states:
                return self.user_states[user_id]
                
            nickname = self._get_unique_nickname()
            user_state = UserState(
                user_id=user_id, 
                own_gender=own_gender, 
                partner_preference=partner_preference, 
                nickname=nickname
            )
            self.user_states[user_id] = user_state
            return user_state
    
    def _get_unique_nickname(self) -> str:
        used_nicknames = {state.nickname for state in self.user_states.values()}
        available = [n for n in NICKNAMES if n not in used_nicknames]
        return random.choice(available if available else NICKNAMES)
    
    async def add_to_queue(self, user_id: int) -> bool:
        """Add user to waiting queue. Returns True if added, False if already waiting/chatting"""
        async with self.lock:
            user_state = self.user_states.get(user_id)
            if not user_state or user_state.is_banned:
                return False
                
            # Check if already in chat or queue
            if user_id in self.active_sessions:
                return False
            
            if user_id in self.waiting_users:
                return False
                
            self.waiting_users.append(user_id)
            return True
    
    async def find_partner(self, user_id: int) -> Optional[int]:
        """Find and match with a chat partner"""
        async with self.lock:
            user_state = self.user_states.get(user_id)
            if not user_state:
                return None
                
            best_partner = None
            max_score = -1
            
            # Find best match based on mutual compatibility and common interests
            for partner_id in self.waiting_users:
                if partner_id == user_id:
                    continue
                    
                partner_state = self.user_states.get(partner_id)
                if not partner_state or partner_state.is_banned:
                    continue
                
                # Check mutual compatibility
                user_wants_partner = (user_state.partner_preference == 'any' or 
                                    user_state.partner_preference == partner_state.own_gender)
                partner_wants_user = (partner_state.partner_preference == 'any' or 
                                    partner_state.partner_preference == user_state.own_gender)
                
                if not (user_wants_partner and partner_wants_user):
                    continue
                    
                # Calculate match score based on common interests
                common_interests = user_state.interests.intersection(partner_state.interests)
                score = len(common_interests)
                
                if score > max_score:
                    best_partner = partner_id
                    max_score = score
            
            if best_partner:
                # Remove both from queue
                if user_id in self.waiting_users:
                    self.waiting_users.remove(user_id)
                if best_partner in self.waiting_users:
                    self.waiting_users.remove(best_partner)
                
                # Create session
                session = ChatSession(user_a=user_id, user_b=best_partner)
                self.active_sessions[user_id] = session
                self.active_sessions[best_partner] = session
                
                # Update stats
                self.user_states[user_id].total_chats += 1
                self.user_states[best_partner].total_chats += 1
                
                return best_partner
            
            return None
    
    async def end_chat(self, user_id: int) -> Optional[int]:
        """End chat session. Returns partner ID if session existed"""
        async with self.lock:
            session = self.active_sessions.get(user_id)
            if not session:
                return None
                
            partner_id = session.user_b if session.user_a == user_id else session.user_a
            
            # Remove session
            self.active_sessions.pop(user_id, None)
            self.active_sessions.pop(partner_id, None)
            
            return partner_id
    
    async def remove_from_queue(self, user_id: int):
        """Remove user from waiting queue"""
        async with self.lock:
            if user_id in self.waiting_users:
                self.waiting_users.remove(user_id)
    
    async def report_user(self, reporter_id: int) -> bool:
        """Report current chat partner"""
        async with self.lock:
            session = self.active_sessions.get(reporter_id)
            if not session:
                return False
                
            partner_id = session.user_b if session.user_a == reporter_id else session.user_a
            partner_state = self.user_states.get(partner_id)
            
            if partner_state:
                partner_state.reported_count += 1
                if partner_state.reported_count >= 3:
                    partner_state.is_banned = True
                    
            return True
    
    def get_partner(self, user_id: int) -> Optional[int]:
        """Get current chat partner"""
        session = self.active_sessions.get(user_id)
        if not session:
            return None
        return session.user_b if session.user_a == user_id else session.user_a
    
    def is_rate_limited(self, user_id: int, limit_seconds: int = 2) -> bool:
        """Check if user is rate limited"""
        now = time.time()
        last_action = self.user_last_action.get(user_id, 0)
        if now - last_action < limit_seconds:
            return True
        self.user_last_action[user_id] = now
        return False

# Global service instance
matchmaking = MatchmakingService()

def contains_forbidden_words(text: str) -> bool:
    """Check if text contains forbidden words"""
    if not text:
        return False
    pattern = r'\b(' + '|'.join(FORBIDDEN_WORDS) + r')\b'
    return re.search(pattern, text.lower()) is not None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with optional deep-link parameters"""
    user_id = update.effective_user.id
    
    # Rate limiting
    if matchmaking.is_rate_limited(user_id):
        return
    
    # Handle deep-link parameters
    args = context.args
    if args:
        if args[0] == 'find':
            await find_partner_flow(update, context)
            return
        elif args[0].startswith('invite_'):
            await handle_invite_link(update, context, args[0])
            return
    
    # Check if user already exists
    user_state = matchmaking.user_states.get(user_id)
    if user_state:
        if matchmaking.get_partner(user_id):
            await update.message.reply_text(Messages.ALREADY_IN_CHAT)
            return
        elif user_id in matchmaking.waiting_users:
            await update.message.reply_text(Messages.ALREADY_WAITING)
            return
    
    # Show gender selection - ask for user's own gender first
    keyboard = [
        [InlineKeyboardButton("👨 I'm Male", callback_data='own_male')],
        [InlineKeyboardButton("👩 I'm Female", callback_data='own_female')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        Messages.WELCOME + "\n\nFirst, what's your gender?", 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def find_partner_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the partner finding flow"""
    user_id = update.effective_user.id
    user_state = matchmaking.user_states.get(user_id)
    
    if not user_state:
        await start(update, context)
        return
    
    if not await matchmaking.add_to_queue(user_id):
        if matchmaking.get_partner(user_id):
            await update.message.reply_text(Messages.ALREADY_IN_CHAT)
        else:
            await update.message.reply_text(Messages.ALREADY_WAITING)
        return
    
    partner_id = await matchmaking.find_partner(user_id)
    
    if partner_id:
        await notify_match(context, user_id, partner_id)
    else:
        await update.message.reply_text(Messages.NO_PARTNER_AVAILABLE)

async def handle_invite_link(update: Update, context: ContextTypes.DEFAULT_TYPE, invite_code: str) -> None:
    """Handle invite deep links"""
    # Extract inviter ID from invite code
    try:
        inviter_id = int(invite_code.split('_')[1])
        await update.message.reply_text(
            f"🎭 You've been invited to chat anonymously! Use /find to start chatting.",
            parse_mode='Markdown'
        )
    except (ValueError, IndexError):
        await start(update, context)

async def set_own_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle own gender selection callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    own_gender = query.data.replace('own_', '')  # Remove 'own_' prefix
    
    # Check if user already exists
    if user_id in matchmaking.user_states:
        await query.edit_message_text(Messages.ALREADY_SET)
        return
    
    # Store own gender temporarily and ask for partner preference
    context.user_data['own_gender'] = own_gender
    
    keyboard = [
        [InlineKeyboardButton("👨 Looking for Males", callback_data='pref_male')],
        [InlineKeyboardButton("👩 Looking for Females", callback_data='pref_female')],
        [InlineKeyboardButton("🌟 No Preference", callback_data='pref_any')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Great! Now, who would you like to chat with?",
        reply_markup=reply_markup
    )

async def set_partner_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle partner preference selection callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    partner_preference = query.data.replace('pref_', '')  # Remove 'pref_' prefix
    own_gender = context.user_data.get('own_gender')
    
    if not own_gender:
        await query.edit_message_text("Something went wrong. Please start over with /start")
        return
    
    # Create user state with both values
    user_state = await matchmaking.create_user(user_id, own_gender, partner_preference)
    
    await query.edit_message_text(
        Messages.GENDER_SET.format(user_state.nickname),
        parse_mode='Markdown'
    )
    
    # Clear temporary data
    context.user_data.clear()
    
    # Add to queue and find partner
    await matchmaking.add_to_queue(user_id)
    partner_id = await matchmaking.find_partner(user_id)
    
    if partner_id:
        await notify_match(context, user_id, partner_id)
    else:
        await context.bot.send_message(user_id, Messages.NO_PARTNER_AVAILABLE)

async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /find command"""
    await find_partner_flow(update, context)

async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /next command (skip current chat)"""
    user_id = update.effective_user.id
    
    if matchmaking.is_rate_limited(user_id):
        return
    
    partner_id = await matchmaking.end_chat(user_id)
    
    if partner_id:
        await update.message.reply_text(Messages.SKIPPED_CHAT)
        await context.bot.send_message(partner_id, Messages.PARTNER_SKIPPED)
        
        # Both users search for new partners
        await matchmaking.add_to_queue(user_id)
        await matchmaking.add_to_queue(partner_id)
        
        user_partner = await matchmaking.find_partner(user_id)
        partner_partner = await matchmaking.find_partner(partner_id)
        
        if user_partner:
            await notify_match(context, user_id, user_partner)
        else:
            await context.bot.send_message(user_id, Messages.NO_PARTNER_AVAILABLE)
            
        if partner_partner:
            await notify_match(context, partner_id, partner_partner)
        else:
            await context.bot.send_message(partner_id, Messages.NO_PARTNER_AVAILABLE)
    else:
        await update.message.reply_text(Messages.NOT_IN_CHAT)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stop command"""
    user_id = update.effective_user.id
    partner_id = await matchmaking.end_chat(user_id)
    
    await matchmaking.remove_from_queue(user_id)
    
    if partner_id:
        await update.message.reply_text(Messages.CHAT_ENDED)
        await context.bot.send_message(partner_id, Messages.CHAT_ENDED_BY_PARTNER)
    else:
        await update.message.reply_text(Messages.CHAT_ENDED)

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /report command"""
    user_id = update.effective_user.id
    
    if await matchmaking.report_user(user_id):
        partner_id = await matchmaking.end_chat(user_id)
        await update.message.reply_text(Messages.REPORT_SENT)
        
        if partner_id:
            await context.bot.send_message(partner_id, Messages.CHAT_ENDED_BY_PARTNER)
    else:
        await update.message.reply_text(Messages.REPORT_ONLY_IN_CHAT)

async def interests_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /interests command"""
    user_id = update.effective_user.id
    user_state = matchmaking.user_states.get(user_id)
    
    if not user_state:
        await update.message.reply_text(Messages.NEED_GENDER_FIRST)
        return
    
    if not context.args:
        await update.message.reply_text(Messages.INTERESTS_HELP)
        return
    
    interests_text = ' '.join(context.args)
    interests = {interest.strip().lower() for interest in interests_text.split(',') if interest.strip()}
    
    user_state.interests = interests
    await update.message.reply_text(
        Messages.INTERESTS_SET.format(', '.join(interests)),
        parse_mode='Markdown'
    )

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /profile command"""
    user_id = update.effective_user.id
    user_state = matchmaking.user_states.get(user_id)
    
    if not user_state:
        await update.message.reply_text(Messages.NEED_GENDER_FIRST)
        return
    
    interests_text = ', '.join(user_state.interests) if user_state.interests else "None set"
    created_date = user_state.created_at.strftime("%B %d, %Y")
    
    profile_text = Messages.PROFILE_INFO.format(
        user_state.nickname,
        f"{user_state.own_gender.title()} looking for {user_state.partner_preference.title()}",
        interests_text,
        user_state.total_chats,
        created_date
    )
    
    await update.message.reply_text(profile_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    await update.message.reply_text(Messages.HELP, parse_mode='Markdown')

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command"""
    user_id = update.effective_user.id
    user_state = matchmaking.user_states.get(user_id)
    
    if not user_state:
        await update.message.reply_text(Messages.NEED_GENDER_FIRST)
        return
    
    keyboard = [
        [InlineKeyboardButton("🔄 Change Gender", callback_data='change_gender')],
        [InlineKeyboardButton("💭 Edit Interests", callback_data='edit_interests')],
        [InlineKeyboardButton("🎭 New Nickname", callback_data='new_nickname')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚙️ **Settings for {user_state.nickname}**\n\nWhat would you like to change?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_state = matchmaking.user_states.get(user_id)
    
    if not user_state:
        await query.edit_message_text(Messages.NEED_GENDER_FIRST)
        return
    
    if query.data == 'change_gender':
        keyboard = [
            [InlineKeyboardButton(Messages.MALE, callback_data='new_male')],
            [InlineKeyboardButton(Messages.FEMALE, callback_data='new_female')],
            [InlineKeyboardButton(Messages.ANY_GENDER, callback_data='new_any')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Choose your new gender preference:", reply_markup=reply_markup)
        
    elif query.data == 'new_nickname':
        old_nickname = user_state.nickname
        user_state.nickname = matchmaking._get_unique_nickname()
        await query.edit_message_text(f"🎭 Nickname changed from **{old_nickname}** to **{user_state.nickname}**!", parse_mode='Markdown')
        
    elif query.data == 'edit_interests':
        interests_text = ', '.join(user_state.interests) if user_state.interests else "None set"
        await query.edit_message_text(
            f"Current interests: {interests_text}\n\nSend /interests followed by your new interests separated by commas.",
            parse_mode='Markdown'
        )
    
    elif query.data.startswith('new_'):
        new_preference = query.data[4:]  # Remove 'new_' prefix
        user_state.partner_preference = new_preference
        await query.edit_message_text(f"✅ Partner preference updated to: **{new_preference.title()}**", parse_mode='Markdown')

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline queries"""
    query = update.inline_query.query.lower()
    
    results = []
    
    # Find chat result
    results.append(
        InlineQueryResultArticle(
            id="find_chat",
            title=Messages.INLINE_FIND_TITLE,
            description=Messages.INLINE_FIND_DESC,
            input_message_content=InputTextMessageContent(
                message_text="🎭 Tap the button below to start anonymous chatting!",
                parse_mode='Markdown'
            ),
            thumb_url="https://via.placeholder.com/64x64/4CAF50/FFFFFF?text=🎭",
            switch_pm_text="Start Anonymous Chat",
            switch_pm_parameter="find"
        )
    )
    
    # Invite result
    user_id = update.effective_user.id
    results.append(
        InlineQueryResultArticle(
            id="invite_chat",
            title=Messages.INLINE_INVITE_TITLE,
            description=Messages.INLINE_INVITE_DESC,
            input_message_content=InputTextMessageContent(
                message_text="💬 Want to chat with me anonymously? Click below to start!",
                parse_mode='Markdown'
            ),
            thumb_url="https://via.placeholder.com/64x64/2196F3/FFFFFF?text=💬",
            switch_pm_text="Chat Anonymously",
            switch_pm_parameter=f"invite_{user_id}"
        )
    )
    
    # Help result
    results.append(
        InlineQueryResultArticle(
            id="help_info",
            title=Messages.INLINE_HELP_TITLE,
            description=Messages.INLINE_HELP_DESC,
            input_message_content=InputTextMessageContent(
                message_text=Messages.HELP,
                parse_mode='Markdown'
            ),
            thumb_url="https://via.placeholder.com/64x64/FF9800/FFFFFF?text=ℹ️"
        )
    )
    
    await update.inline_query.answer(results, cache_time=300)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all non-command messages"""
    user_id = update.effective_user.id
    
    # Rate limiting
    if matchmaking.is_rate_limited(user_id, 1):
        return
    
    partner_id = matchmaking.get_partner(user_id)
    
    if not partner_id:
        await update.message.reply_text(Messages.NOT_CONNECTED)
        return
    
    user_state = matchmaking.user_states.get(user_id)
    if not user_state:
        await update.message.reply_text(Messages.NOT_CONNECTED)
        return
    
    # Forward message to partner with all media types
    await forward_message_to_partner(update.message, context, user_id, partner_id, user_state.nickname)

async def forward_message_to_partner(message: Message, context: ContextTypes.DEFAULT_TYPE, 
                                   sender_id: int, partner_id: int, nickname: str) -> None:
    """Forward any type of message to chat partner"""
    try:
        # Handle different message types
        if message.text:
            # Check for forbidden words in text
            if contains_forbidden_words(message.text):
                await context.bot.send_message(sender_id, Messages.FORBIDDEN_MESSAGE)
                return
            await context.bot.send_message(partner_id, f"**{nickname}**: {message.text}", parse_mode='Markdown')
        
        elif message.photo:
            caption = f"**{nickname}** sent a photo"
            if message.caption and not contains_forbidden_words(message.caption):
                caption += f": {message.caption}"
            await context.bot.send_photo(partner_id, message.photo[-1].file_id, caption=caption, parse_mode='Markdown')
        
        elif message.voice:
            caption = f"**{nickname}** sent a voice message"
            await context.bot.send_voice(partner_id, message.voice.file_id, caption=caption, parse_mode='Markdown')
        
        elif message.audio:
            caption = f"**{nickname}** sent audio"
            if message.caption and not contains_forbidden_words(message.caption):
                caption += f": {message.caption}"
            await context.bot.send_audio(partner_id, message.audio.file_id, caption=caption, parse_mode='Markdown')
        
        elif message.document:
            caption = f"**{nickname}** sent a document"
            if message.caption and not contains_forbidden_words(message.caption):
                caption += f": {message.caption}"
            await context.bot.send_document(partner_id, message.document.file_id, caption=caption, parse_mode='Markdown')
        
        elif message.video:
            caption = f"**{nickname}** sent a video"
            if message.caption and not contains_forbidden_words(message.caption):
                caption += f": {message.caption}"
            await context.bot.send_video(partner_id, message.video.file_id, caption=caption, parse_mode='Markdown')
        
        elif message.video_note:
            await context.bot.send_video_note(partner_id, message.video_note.file_id)
            await context.bot.send_message(partner_id, f"**{nickname}** sent a video message", parse_mode='Markdown')
        
        elif message.sticker:
            await context.bot.send_sticker(partner_id, message.sticker.file_id)
            await context.bot.send_message(partner_id, f"**{nickname}** sent a sticker", parse_mode='Markdown')
        
        elif message.animation:
            caption = f"**{nickname}** sent a GIF"
            if message.caption and not contains_forbidden_words(message.caption):
                caption += f": {message.caption}"
            await context.bot.send_animation(partner_id, message.animation.file_id, caption=caption, parse_mode='Markdown')
        
        elif message.location:
            await context.bot.send_location(partner_id, message.location.latitude, message.location.longitude)
            await context.bot.send_message(partner_id, f"**{nickname}** shared their location", parse_mode='Markdown')
        
        elif message.contact:
            await context.bot.send_contact(partner_id, message.contact.phone_number, message.contact.first_name,
                                         last_name=message.contact.last_name)
            await context.bot.send_message(partner_id, f"**{nickname}** shared a contact", parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")
        await context.bot.send_message(sender_id, "Failed to send message to your chat partner.")

async def notify_match(context: ContextTypes.DEFAULT_TYPE, user_id: int, partner_id: int) -> None:
    """Notify both users when they're matched"""
    user_state = matchmaking.user_states.get(user_id)
    partner_state = matchmaking.user_states.get(partner_id)
    
    if not user_state or not partner_state:
        return
    
    # Check for common interests
    common_interests = user_state.interests.intersection(partner_state.interests)
    interests_msg = Messages.COMMON_INTERESTS.format(', '.join(common_interests)) if common_interests else ""
    
    # Create inline keyboards for quick actions
    keyboard = [
        [InlineKeyboardButton("⏭️ Next", callback_data="quick_next")],
        [InlineKeyboardButton("🛑 Stop", callback_data="quick_stop")],
        [InlineKeyboardButton("🚨 Report", callback_data="quick_report")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Notify both users
    user_msg = Messages.PARTNER_FOUND.format(partner_state.nickname) + interests_msg
    partner_msg = Messages.PARTNER_FOUND.format(user_state.nickname) + interests_msg
    
    await context.bot.send_message(user_id, user_msg, reply_markup=reply_markup, parse_mode='Markdown')
    await context.bot.send_message(partner_id, partner_msg, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_quick_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quick action buttons"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action = query.data
    
    if action == "quick_next":
        # Simulate /next command
        await next_command_for_user(context, user_id)
    elif action == "quick_stop":
        # Simulate /stop command  
        await stop_command_for_user(context, user_id)
    elif action == "quick_report":
        # Simulate /report command
        await report_command_for_user(context, user_id)
    
    # Remove the inline keyboard
    await query.edit_message_reply_markup(reply_markup=None)

async def next_command_for_user(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Execute next command for a user"""
    partner_id = await matchmaking.end_chat(user_id)
    
    if partner_id:
        await context.bot.send_message(user_id, Messages.SKIPPED_CHAT)
        await context.bot.send_message(partner_id, Messages.PARTNER_SKIPPED)
        
        # Both users search for new partners
        await matchmaking.add_to_queue(user_id)
        await matchmaking.add_to_queue(partner_id)
        
        user_partner = await matchmaking.find_partner(user_id)
        partner_partner = await matchmaking.find_partner(partner_id)
        
        if user_partner:
            await notify_match(context, user_id, user_partner)
        else:
            await context.bot.send_message(user_id, Messages.NO_PARTNER_AVAILABLE)
            
        if partner_partner:
            await notify_match(context, partner_id, partner_partner)
        else:
            await context.bot.send_message(partner_id, Messages.NO_PARTNER_AVAILABLE)

async def stop_command_for_user(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Execute stop command for a user"""
    partner_id = await matchmaking.end_chat(user_id)
    await matchmaking.remove_from_queue(user_id)
    
    if partner_id:
        await context.bot.send_message(user_id, Messages.CHAT_ENDED)
        await context.bot.send_message(partner_id, Messages.CHAT_ENDED_BY_PARTNER)
    else:
        await context.bot.send_message(user_id, Messages.CHAT_ENDED)

async def report_command_for_user(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Execute report command for a user"""
    if await matchmaking.report_user(user_id):
        partner_id = await matchmaking.end_chat(user_id)
        await context.bot.send_message(user_id, Messages.REPORT_SENT)
        
        if partner_id:
            await context.bot.send_message(partner_id, Messages.CHAT_ENDED_BY_PARTNER)
    else:
        await context.bot.send_message(user_id, Messages.REPORT_ONLY_IN_CHAT)

def main() -> None:
    """Start the bot"""
    application = Application.builder().token(TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('find', find_command))
    application.add_handler(CommandHandler('next', next_command))
    application.add_handler(CommandHandler('stop', stop_command))
    application.add_handler(CommandHandler('report', report_command))
    application.add_handler(CommandHandler('interests', interests_command))
    application.add_handler(CommandHandler('profile', profile_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('settings', settings_command))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(set_own_gender, pattern='^own_(male|female)$'))
    application.add_handler(CallbackQueryHandler(set_partner_preference, pattern='^pref_(male|female|any)$'))
    application.add_handler(CallbackQueryHandler(handle_settings_callback, pattern='^(change_gender|new_nickname|edit_interests|new_male|new_female|new_any)$'))
    application.add_handler(CallbackQueryHandler(handle_quick_actions, pattern='^(quick_next|quick_stop|quick_report)$'))
    
    # Inline query handler
    application.add_handler(InlineQueryHandler(handle_inline_query))
    
    # Message handlers (handle all media types)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message
    ))
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.VOICE | filters.AUDIO | filters.Document.ALL | 
        filters.VIDEO | filters.VIDEO_NOTE | filters.Sticker.ALL | filters.ANIMATION |
        filters.LOCATION | filters.CONTACT, handle_message
    ))
    
    logger.info("Starting Anonymous Chat Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()