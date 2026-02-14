"""
Vercel Serverless Function for Telegram Bot Webhook
This handles incoming webhook requests from Telegram
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path to import bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Check environment variables first
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set")

if not DATABASE_URL:
    logger.error("DATABASE_URL not set")

# Now import telegram modules
from telegram import Update
from telegram.ext import Application

# Import handlers
try:
    from anonymous_chat_bot import (
        start,
        find_partner_command,
        skip_command,
        stop_command,
        report_command,
        profile_command,
        help_command,
        privacy_command,
        button_callback,
        handle_message,
        handle_photo,
        viewonce_command,
    )

    HANDLERS_IMPORTED = True
except Exception as e:
    logger.error(f"Failed to import handlers: {e}")
    HANDLERS_IMPORTED = False

# Initialize database
try:
    import database

    database.init_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")


def get_application():
    """Get or create the application instance"""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    if HANDLERS_IMPORTED:
        from telegram.ext import (
            CommandHandler,
            CallbackQueryHandler,
            MessageHandler,
            filters,
        )

        # Add all command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("find", find_partner_command))
        application.add_handler(CommandHandler("skip", skip_command))
        application.add_handler(CommandHandler("stop", stop_command))
        application.add_handler(CommandHandler("report", report_command))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("privacy", privacy_command))
        application.add_handler(CommandHandler("viewonce", viewonce_command))

        # Add callback and message handlers
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )

        logger.info("All handlers registered successfully")

    return application


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""

    def do_POST(self):
        """Handle POST requests from Telegram webhook"""
        try:
            # Get request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            # Parse update from Telegram
            update_data = json.loads(body.decode("utf-8"))
            logger.info(f"Received update: {update_data.get('update_id', 'unknown')}")

            # Get application instance
            app = get_application()

            # Create update object
            update = Update.de_json(update_data, app.bot)

            # Initialize and process update asynchronously
            async def process():
                async with app:
                    await app.initialize()
                    await app.process_update(update)
                    await app.shutdown()

            asyncio.run(process())

            # Send success response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        except Exception as e:
            logger.error(f"Error processing update: {e}", exc_info=True)
            # Send error response
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            error_response = {"ok": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())

    def do_GET(self):
        """Handle GET requests - show bot status"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        status = {
            "status": "running",
            "bot_token_set": bool(TELEGRAM_BOT_TOKEN),
            "database_url_set": bool(DATABASE_URL),
            "handlers_loaded": HANDLERS_IMPORTED,
        }

        self.wfile.write(json.dumps(status).encode())
