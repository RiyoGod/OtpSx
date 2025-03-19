import os
import asyncio
from telethon import TelegramClient, events, Button
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError,
    FloodWaitError, PhoneNumberBannedError, UserDeactivatedBanError, PhoneNumberInvalidError
)
from config import API_ID, API_HASH, OWNER_ID, BOT_TOKEN

print("✅ Import successful. Starting bot...")  # Debug print

# Start bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Dictionary to store login attempts
login_sessions = {}

# Error logging function
async def send_error_log(error):
    try:
        await bot.send_message(OWNER_ID, f"⚠️ **Error Occurred:**\n\n`{error}`")
    except Exception as e:
        print(f"❌ Failed to send error log: {e}")

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    print(f"⚡ Received /start from {event.sender_id}")  # Debug print
    
    if event.sender_id != OWNER_ID:
        await event.reply("🚫 **You are not authorized to use this bot.**")
        return
    
    await event.reply(
        "**🚀 Welcome to the Telegram Login Bot!**\n\n"
        "Click below to login.",
        buttons=[[Button.text("Login Account", resize=True)]]
    )

@bot.on(events.NewMessage(pattern="Login Account"))
async def login_step_1(event):
    print(f"📩 {event.sender_id} started login process.")  # Debug print

    if event.sender_id != OWNER_ID:
        await event.respond("🚫 **Only the owner can log in accounts.**")
        return

    await event.respond("**📞 Send the phone number you want to log in with:**")

@bot.on(events.NewMessage)
async def handle_message(event):
    try:
        text = event.raw_text.strip()
        
        if text.startswith("+") and event.sender_id == OWNER_ID:
            print(f"📞 Received number: {text} from {event.sender_id}")

            if event.sender_id in login_sessions:
                await event.respond("⚠️ **A login process is already in progress!**")
                return
            
            login_sessions[event.sender_id] = {"phone": text}
            
            new_client = TelegramClient(f"sessions/{text}", API_ID, API_HASH)
            await new_client.connect()
            
            if not await new_client.is_user_authorized():
                code = await new_client.send_code_request(text)
                await event.respond(f"📩 **OTP sent to `{text}`.**\n\n📥 Send the OTP:")
                login_sessions[event.sender_id]["client"] = new_client
            else:
                await event.respond("✅ **This number is already logged in.**")
                await new_client.disconnect()
                del login_sessions[event.sender_id]

        elif event.sender_id in login_sessions and "client" in login_sessions[event.sender_id]:
            client = login_sessions[event.sender_id]["client"]
            
            try:
                await client.sign_in(login_sessions[event.sender_id]["phone"], text)
                await event.respond("✅ **Login successful!**\n\n🔧 Removing privacy restrictions...")
                
                # Remove privacy settings
                await client(UpdatePrivacyRequest(
                    key=InputPrivacyKeyPhoneNumber(),
                    rules=[InputPrivacyValueAllowAll()]
                ))

                await event.respond("🔓 **Privacy settings disabled!**")
                del login_sessions[event.sender_id]

            except SessionPasswordNeededError:
                await event.respond("🔒 **Account has 2-step verification.**\nSend the password:")
                login_sessions[event.sender_id]["password_needed"] = True

            except PhoneCodeInvalidError:
                await event.respond("❌ **Invalid OTP! Please send the correct one.**")

            except PhoneCodeExpiredError:
                await event.respond("⏳ **OTP expired! Restarting login process.**")
                del login_sessions[event.sender_id]

            except Exception as e:
                await send_error_log(str(e))
                del login_sessions[event.sender_id]

        elif event.sender_id in login_sessions and "password_needed" in login_sessions[event.sender_id]:
            client = login_sessions[event.sender_id]["client"]
            
            try:
                await client.sign_in(password=text)
                await event.respond("✅ **2-Step Password Accepted!**\n\n🔧 Removing privacy restrictions...")
                
                await client(UpdatePrivacyRequest(
                    key=InputPrivacyKeyPhoneNumber(),
                    rules=[InputPrivacyValueAllowAll()]
                ))

                await event.respond("🔓 **Privacy settings disabled!**")
                del login_sessions[event.sender_id]

            except Exception as e:
                await send_error_log(str(e))
                del login_sessions[event.sender_id]

        else:
            await event.respond("🚫 **Invalid command.** Use `/start` to begin.")

    except Exception as e:
        print(f"❌ Error: {e}")  # Debug print
        await send_error_log(str(e))

print("✅ Bot is running. Waiting for messages...")  # Debug print

bot.run_until_disconnected()
