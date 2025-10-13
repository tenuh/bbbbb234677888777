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
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

if not DATABASE_URL:
    logger.error("DATABASE_URL not set")
    raise ValueError("DATABASE_URL environment variable not set")

# Now import database and telegram modules
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import database

# Initialize database
try:
    database.init_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    # Don't raise, allow the handler to work even if DB fails initially

# Create application instance (but don't initialize yet)
application = None

def get_application():
    """Get or create the application instance"""
    global application
    if application is None:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Import and setup all handlers from main bot file
        try:
            from anonymous_chat_bot import (
                start, find_partner_command, skip_command, stop_command,
                report_command, profile_command, help_command, privacy_command,
                button_callback, handle_message, handle_photo, viewonce_command
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
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            
            logger.info("All handlers registered successfully")
        except Exception as e:
            logger.error(f"Failed to import or register handlers: {e}")
            raise
    
    return application


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""
    
    def do_POST(self):
        """Handle POST requests from Telegram webhook"""
        try:
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Parse update from Telegram
            update_data = json.loads(body.decode('utf-8'))
            logger.info(f"Received update: {update_data.get('update_id', 'unknown')}")
            
            # Get application instance
            app = get_application()
            
            # Create update object
            update = Update.de_json(update_data, app.bot)
            
            # Initialize and process update asynchronously
            async def process():
                async with app:
                    await app.process_update(update)
            
            asyncio.run(process())
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            logger.error(f"Error processing update: {e}", exc_info=True)
            # Send error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"ok": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_GET(self):
        """Handle GET requests - show bot status"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Telegram Bot</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    text-align: center;
                    padding: 2rem;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                }
                h1 { margin: 0; font-size: 2.5rem; }
                p { font-size: 1.2rem; opacity: 0.9; }
                .emoji { font-size: 4rem; margin: 1rem 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="emoji">🤖</div>
                <h1>Telegram Bot is Running!</h1>
                <p>Anonymous Chat Bot - Webhook Mode</p>
                <p>✅ Ready to receive updates</p>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
