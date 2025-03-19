import os
import asyncio
import logging
from telethon import TelegramClient, events, Button
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError,
    FloodWaitError, PhoneNumberBannedError, UserDeactivatedBanError, PhoneNumberInvalidError
)
from config import API_ID, API_HASH, OWNER_ID, BOT_TOKEN

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot client
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Store active login requests
active_logins = {}

async def send_error_log(error_text):
    """Send error logs to owner."""
    await bot.send_message(OWNER_ID, f"⚠️ **Error Occurred:**\n\n`{error_text}`")

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Handle /start command."""
    if event.sender_id != OWNER_ID:
        return  # Ignore messages from non-owner users
    
    buttons = [
        Button.inline("🔑 Add Account", b"add_account"),
        Button.inline("📜 View Sessions", b"view_sessions")
    ]
    await event.respond("**🤖 Welcome to the OTP Manager Bot!**\n\nManage multiple Telegram accounts securely.", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    """Handle inline button clicks."""
    if event.sender_id != OWNER_ID:
        return
    
    data = event.data.decode()
    if data == "add_account":
        await event.respond("📞 **Send the phone number to login:**")
        active_logins[event.sender_id] = "waiting_for_number"
    elif data == "view_sessions":
        sessions = os.listdir("sessions")
        if not sessions:
            await event.respond("❌ **No active sessions found!**")
        else:
            session_list = "\n".join(sessions)
            await event.respond(f"📜 **Active Sessions:**\n\n`{session_list}`")

@bot.on(events.NewMessage)
async def handle_message(event):
    """Handle phone number input for login."""
    if event.sender_id != OWNER_ID:
        return

    if event.sender_id in active_logins and active_logins[event.sender_id] == "waiting_for_number":
        phone_number = event.text
        await event.respond(f"📲 **Logging in with** `{phone_number}`...\nPlease wait.")
        await login_account(event, phone_number)
        del active_logins[event.sender_id]

async def login_account(event, phone):
    """Login process for a new account."""
    session_name = f"sessions/{phone}.session"
    client = TelegramClient(session_name, API_ID, API_HASH)

    try:
        await client.connect()
        if await client.is_user_authorized():
            await event.respond("✅ **Already logged in!**")
            return
        
        code = await client.send_code_request(phone)
        await event.respond("📩 **OTP sent! Check your Telegram SMS.**\nReply with the code.")

        active_logins[event.sender_id] = {"client": client, "phone": phone}

    except PhoneNumberBannedError:
        await event.respond("🚫 **This phone number is banned! Try another one.**")
    except PhoneNumberInvalidError:
        await event.respond("🚫 **Invalid phone number! Please check again.**")
    except FloodWaitError as e:
        await event.respond(f"⏳ **Too many attempts! Try again after {e.seconds} seconds.**")
    except Exception as e:
        await send_error_log(f"SendCodeRequest Error: {str(e)}")

@bot.on(events.NewMessage)
async def handle_otp(event):
    """Handle OTP input from owner."""
    if event.sender_id != OWNER_ID:
        return

    if event.sender_id in active_logins and isinstance(active_logins[event.sender_id], dict):
        client = active_logins[event.sender_id]["client"]
        phone = active_logins[event.sender_id]["phone"]
        code = event.text

        try:
            await client.sign_in(phone, code)
            await event.respond("✅ **Login successful!**")
            del active_logins[event.sender_id]
        except PhoneCodeInvalidError:
            await event.respond("❌ **Invalid code! Try again.**")
        except PhoneCodeExpiredError:
            await event.respond("⏳ **Code expired! Restart login.**")
        except SessionPasswordNeededError:
            await event.respond("🔒 **Account has 2FA enabled! Send the password.**")
            active_logins[event.sender_id]["2fa"] = True
        except Exception as e:
            await send_error_log(f"OTP Error: {str(e)}")

@bot.on(events.NewMessage)
async def handle_2fa(event):
    """Handle 2FA password input."""
    if event.sender_id != OWNER_ID:
        return

    if event.sender_id in active_logins and active_logins[event.sender_id].get("2fa"):
        client = active_logins[event.sender_id]["client"]
        password = event.text

        try:
            await client.sign_in(password=password)
            await event.respond("✅ **Login successful with 2FA!**")
            del active_logins[event.sender_id]
        except Exception as e:
            await send_error_log(f"2FA Error: {str(e)}")

print("🚀 Bot is running...")
bot.run_until_disconnected()
