import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")