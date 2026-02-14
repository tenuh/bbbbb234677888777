import logging
import os
from typing import Dict, Optional, Set

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import database

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

waiting_users: Set[int] = set()
active_chats: Dict[int, int] = {}


def _chat_controls() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⏭️ Skip", callback_data="skip")],
            [InlineKeyboardButton("⏹️ Stop", callback_data="stop")],
            [InlineKeyboardButton("🚨 Report", callback_data="report")],
        ]
    )


def _main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 Find Partner", callback_data="find")],
            [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
            [InlineKeyboardButton("❓ Help", callback_data="help")],
        ]
    )


def _get_or_create_user(db, update: Update):
    tg_user = update.effective_user
    user = database.get_user(db, tg_user.id)
    if user:
        database.update_user_activity(db, tg_user.id)
        return user

    nickname = tg_user.first_name or tg_user.username or f"user_{tg_user.id}"
    return database.create_user(
        db=db,
        user_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
        gender="male",
        nickname=nickname,
    )


async def _end_chat(
    context: ContextTypes.DEFAULT_TYPE, user_id: int, notify: str
) -> None:
    partner_id = active_chats.pop(user_id, None)
    if partner_id is None:
        return
    active_chats.pop(partner_id, None)
    waiting_users.discard(user_id)
    waiting_users.discard(partner_id)
    await context.bot.send_message(chat_id=user_id, text=notify)
    await context.bot.send_message(
        chat_id=partner_id, text="😔 Your chat partner left the chat."
    )


async def _try_match(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> Optional[int]:
    for candidate in list(waiting_users):
        if candidate != user_id:
            waiting_users.discard(user_id)
            waiting_users.discard(candidate)
            active_chats[user_id] = candidate
            active_chats[candidate] = user_id
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 Partner found. Say hi!",
                reply_markup=_chat_controls(),
            )
            await context.bot.send_message(
                chat_id=candidate,
                text="🎉 Partner found. Say hi!",
                reply_markup=_chat_controls(),
            )
            return candidate
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with database.get_db() as db:
        user = _get_or_create_user(db, update)

    if user.is_banned:
        await update.message.reply_text("❌ Your account is suspended.")
        return

    await update.message.reply_text(
        "🎭 Welcome to Anonymous Chat Bot!", reply_markup=_main_menu()
    )


async def find_partner_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user_id = update.effective_user.id
    if user_id in active_chats:
        await update.message.reply_text("❌ You're already in a chat.")
        return

    if user_id in waiting_users:
        await update.message.reply_text("⏳ Already searching for a partner...")
        return

    waiting_users.add(user_id)
    matched = await _try_match(context, user_id)
    if not matched:
        await update.message.reply_text("🔍 Searching for a chat partner...")


async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in active_chats:
        await update.message.reply_text("❌ You're not currently in a chat.")
        return

    await _end_chat(context, user_id, "⏭️ You skipped this chat.")
    waiting_users.add(user_id)
    await _try_match(context, user_id)


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in waiting_users:
        waiting_users.discard(user_id)
        await update.message.reply_text("⏹️ Search stopped.")
        return
    if user_id in active_chats:
        await _end_chat(context, user_id, "⏹️ Chat ended.")
        return
    await update.message.reply_text("❌ You're not in a chat.")


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    partner = active_chats.get(user_id)
    if not partner:
        await update.message.reply_text(
            "⚠️ Reports are only available during an active chat."
        )
        return

    with database.get_db() as db:
        database.create_user_report(db, reporter_id=user_id, reported_id=partner)

    await _end_chat(context, user_id, "✅ Report sent. Chat ended.")


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with database.get_db() as db:
        user = database.get_user(db, update.effective_user.id)
    if not user:
        await update.message.reply_text("No profile found. Use /start first.")
        return

    await update.message.reply_text(
        f"👤 Profile\nNickname: {user.nickname}\nGender: {user.gender}\nTotal chats: {user.total_chats}"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Use /find to start matching, /skip to switch partner, /stop to end chat."
    )


async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "We relay your messages anonymously and store minimal profile and moderation data."
    )


async def viewonce_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "View-once mode is not available in this deployment."
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    if query.data == "find":
        if user_id in active_chats:
            await query.message.reply_text("❌ You're already in a chat.")
            return
        if user_id in waiting_users:
            await query.message.reply_text("⏳ Already searching for a partner...")
            return
        waiting_users.add(user_id)
        matched = await _try_match(context, user_id)
        if not matched:
            await query.message.reply_text("🔍 Searching for a chat partner...")
        return

    if query.data == "skip":
        if user_id not in active_chats:
            await query.message.reply_text("❌ You're not currently in a chat.")
            return
        await _end_chat(context, user_id, "⏭️ You skipped this chat.")
        waiting_users.add(user_id)
        await _try_match(context, user_id)
        return

    if query.data == "stop":
        if user_id in waiting_users:
            waiting_users.discard(user_id)
            await query.message.reply_text("⏹️ Search stopped.")
            return
        if user_id in active_chats:
            await _end_chat(context, user_id, "⏹️ Chat ended.")
            return
        await query.message.reply_text("❌ You're not in a chat.")
        return

    if query.data == "report":
        partner = active_chats.get(user_id)
        if not partner:
            await query.message.reply_text("⚠️ Reports are only available during an active chat.")
            return
        with database.get_db() as db:
            database.create_user_report(db, reporter_id=user_id, reported_id=partner)
        await _end_chat(context, user_id, "✅ Report sent. Chat ended.")
        return

    if query.data == "profile":
        with database.get_db() as db:
            user = database.get_user(db, user_id)
        if not user:
            await query.message.reply_text("No profile found. Use /start first.")
            return
        await query.message.reply_text(
            f"👤 Profile\nNickname: {user.nickname}\nGender: {user.gender}\nTotal chats: {user.total_chats}"
        )
        return

    if query.data == "help":
        await query.message.reply_text(
            "Use /find to start matching, /skip to switch partner, /stop to end chat."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    partner = active_chats.get(user_id)
    if not partner:
        await update.message.reply_text("Use /find to connect with a partner.")
        return
    await context.bot.send_message(chat_id=partner, text=update.message.text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    partner = active_chats.get(user_id)
    if not partner:
        await update.message.reply_text("Use /find to connect with a partner.")
        return
    await context.bot.forward_message(
        chat_id=partner,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
    )
