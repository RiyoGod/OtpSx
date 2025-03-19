import os
from dotenv import load_dotenv

# Load environment variables from .env file (if exists)
load_dotenv()

# 🔹 TELEGRAM API Credentials
API_ID = 26416419  # Replace with your Telegram API ID
API_HASH = "c109c77f5823c847b1aeb7fbd4990cc4"  # Replace with your Telegram API Hash

# 🔹 BOT Credentials
BOT_TOKEN = "7955234990:AAH91z9G-Ytz3xGhil7Ermy0l9NvOJufEFQ"  # Replace with your Bot Token from @BotFather

# 🔹 OWNER Information (Your Telegram User ID)
OWNER_ID = 6748827895  # Replace with your Telegram User ID (Owner)

# 🔹 SESSION MANAGEMENT
SESSION_PATH = "sessions/"  # Folder to store login sessions
AUTO_REMOVE_2FA = True  # Automatically disable 2FA (if possible)

# 🔹 SECURITY & LOGIN SETTINGS
LOGIN_TIMEOUT = 300  # Timeout for OTP (in seconds)
MAX_RETRIES = 3  # Max OTP attempts before failing
ALLOW_PUBLIC_USE = False  # If False, only OWNER can use

# 🔹 LOGGING SETTINGS
LOGGING_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR

# 🔹 INLINE BUTTON TEXTS (For Custom UI)
BUTTONS = {
    "add_account": "📲 Add Account",
    "enter_otp": "🔑 Enter OTP",
    "cancel": "❌ Cancel",
}
