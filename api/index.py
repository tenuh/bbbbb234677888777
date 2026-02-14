from http.server import BaseHTTPRequestHandler
import json
import os


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        # Check environment variables (without exposing values)
        env_status = {
            "bot_token_set": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "database_url_set": bool(os.getenv("DATABASE_URL")),
            "status": "ready",
        }

        self.wfile.write(json.dumps(env_status, indent=2).encode())
