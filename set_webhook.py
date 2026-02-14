#!/usr/bin/env python3
"""
Set Telegram Webhook for Vercel Deployment
Run this after deploying to Vercel to set the webhook URL
"""

import requests
import os
import sys


def set_webhook(bot_token, webhook_url):
    """Set the webhook for the Telegram bot"""

    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"

    print(f"🔗 Setting webhook to: {webhook_url}")

    response = requests.post(
        api_url,
        json={
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query", "edited_message"],
        },
    )

    result = response.json()

    if result.get("ok"):
        print("✅ Webhook set successfully!")
        print(f"📝 Description: {result.get('description', 'Success')}")
    else:
        print("❌ Failed to set webhook!")
        print(f"📝 Error: {result.get('description', 'Unknown error')}")
        sys.exit(1)

    return result


def get_webhook_info(bot_token):
    """Get current webhook information"""

    api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"

    response = requests.get(api_url)
    result = response.json()

    if result.get("ok"):
        info = result.get("result", {})
        print("\n📊 Current Webhook Info:")
        print(f"   URL: {info.get('url', 'Not set')}")
        print(f"   Pending updates: {info.get('pending_update_count', 0)}")
        print(f"   Last error: {info.get('last_error_message', 'None')}")
        print(f"   Max connections: {info.get('max_connections', 40)}")

        if info.get("last_error_date"):
            import datetime

            error_date = datetime.datetime.fromtimestamp(info["last_error_date"])
            print(f"   Last error date: {error_date}")

    return result


def main():
    """Main function"""

    print("🤖 Telegram Bot Webhook Setup")
    print("=" * 50)

    # Get bot token from environment or prompt
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        bot_token = input("\n🔑 Enter your Telegram Bot Token: ").strip()

    if not bot_token:
        print("❌ Bot token is required!")
        sys.exit(1)

    # Get Vercel URL
    vercel_url = input(
        "\n🌐 Enter your Vercel deployment URL (e.g., https://your-app.vercel.app): "
    ).strip()

    if not vercel_url:
        print("❌ Vercel URL is required!")
        sys.exit(1)

    # Ensure URL has https://
    if not vercel_url.startswith("http"):
        vercel_url = f"https://{vercel_url}"

    # Add webhook endpoint
    webhook_url = f"{vercel_url}/api/webhook"

    # Set webhook
    set_webhook(bot_token, webhook_url)

    # Get webhook info
    print("\n" + "=" * 50)
    get_webhook_info(bot_token)

    print("\n✨ Done! Your bot should now receive updates via webhook.")
    print("📱 Test it by sending a message to your bot on Telegram!")


if __name__ == "__main__":
    main()
