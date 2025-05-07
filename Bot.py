# (Unchanged import section)
import json
import os
import random
import string
import time
from datetime import datetime, timedelta

from telegram import (
    Bot,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ChatInviteLink,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

TOKEN = "7949540768:AAETDVvHgOHZiNpan_jJAvRB9NsB-u3256k"
ADMIN_ID = 6366135368 

DATA_FILE = "data.json"
MAX_CHANNELS = 200
INVITE_EXPIRY_SECONDS = 60
RENEW_THRESHOLD_SECONDS = 10


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def generate_code(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    data = load_data()

    if args:
        code = args[0]
        for channel_id, details in data.items():
            if details.get("code") == code:
                invite_info = details.get("invite_info", {})
                current_time = int(time.time())
                invite_link = invite_info.get("link")
                expiry = invite_info.get("expiry", 0)

                if invite_link and current_time < expiry:
                    if expiry - current_time <= RENEW_THRESHOLD_SECONDS:
                        new_invite = await context.bot.create_chat_invite_link(
                            chat_id=int(channel_id),
                            expire_date=current_time + INVITE_EXPIRY_SECONDS
                        )
                        invite_link = new_invite.invite_link
                        expiry = current_time + INVITE_EXPIRY_SECONDS
                        details["invite_info"] = {"link": invite_link, "expiry": expiry}
                        save_data(data)
                else:
                    new_invite = await context.bot.create_chat_invite_link(
                        chat_id=int(channel_id),
                        expire_date=current_time + INVITE_EXPIRY_SECONDS
                    )
                    invite_link = new_invite.invite_link
                    expiry = current_time + INVITE_EXPIRY_SECONDS
                    details["invite_info"] = {"link": invite_link, "expiry": expiry}
                    save_data(data)

                keyboard = [[InlineKeyboardButton("🔔 Request to Join", url=invite_link)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Here is your link! Click below 👇", reply_markup=reply_markup)
                return

        await update.message.reply_text("⚠️ Invalid code or channel not found.")
    else:
        if user_id != ADMIN_ID:
            await update.message.reply_text("⚠️ You are not authorized to use this bot. Please buy your own bot from - @Zenxuuh")
        else:
            await update.message.reply_text("👑 Welcome, Admin! Use /help to see available commands.")


async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ You are not authorized to use this bot. Please buy your own bot from - @Zenxuuh")
        return ConversationHandler.END

    data = load_data()
    if len(data) >= MAX_CHANNELS:
        await update.message.reply_text("⚠️ You have reached the maximum number of channels.")
        return ConversationHandler.END

    await update.message.reply_text("📥 Send me the channel UID (must start with this symbol ' - ' ).")
    return 1


async def receive_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_id = update.message.text.strip()
    data = load_data()

    if not channel_id.startswith("-100") or not channel_id[1:].isdigit():
        await update.message.reply_text("⚠️ Invalid channel ID. It must start with -100 followed by digits.")
        return ConversationHandler.END

    if channel_id in data:
        await update.message.reply_text("⚠️ This channel is already added.")
        return ConversationHandler.END

    code = generate_code()
    data[channel_id] = {
        "code": code,
        "invite_info": {}
    }
    save_data(data)

    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start={code}"
    await update.message.reply_text(f"✅ Channel added!\n\nUnique link: {referral_link}")
    return ConversationHandler.END


async def delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ You are not authorized to use this bot. Please buy your own bot from - @Zenxuuh")
        return

    args = context.args
    if not args:
        await update.message.reply_text("🛠 Usage: `/del` <channel_id>")
        return

    data = load_data()
    channel_id = args[0]
    if channel_id in data:
        del data[channel_id]
        save_data(data)
        await update.message.reply_text("🧹 Channel removed successfully.")
    else:
        await update.message.reply_text("⚠️ Channel not found.")


async def delete_all_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ You are not authorized to use this bot. Please buy your own bot from - @Zenxuuh")
        return ConversationHandler.END

    await update.message.reply_text("⚠️ Are you sure you want to delete all channels? Type 'yes' to confirm.")
    return 2


async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower().strip() == "yes":
        save_data({})
        await update.message.reply_text("🧹 All channels have been deleted.")
    else:
        await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END


async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ You are not authorized to use this bot. Please buy your own bot from - @Zenxuuh")
        return

    data = load_data()
    if not data:
        await update.message.reply_text("⚠️ No channels added yet.")
        return

    message = "📋 *Channels List:*\n"
    bot_username = context.bot.username
    for channel_id, details in data.items():
        code = details.get("code")
        referral_link = f"https://t.me/{bot_username}?start={code}"
        message += f"\n• Channel ID: `{channel_id}`\n  Link: {referral_link}\n"

    await update.message.reply_text(message, parse_mode="Markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ You are not authorized to use this bot. Please buy your own bot from - @Zenxuuh")
        return

    help_text = (
        "*🛠 Admin Commands:*\n\n"
        "➕ /add – Add a new channel\n"
        "➖ `/del` \\[channel\\_id\\] – Delete a specific channel\n"
        "🗑️ /delall – Delete all channels\n"
        "📋 /list – List all channels\n"
        "❌ /cancel – Cancel the current action\n"
        "ℹ️ /help – Show this help menu"
    )

    await update.message.reply_text(help_text, parse_mode="MarkdownV2")

def main():
    app = Application.builder().token(TOKEN).build()

    add_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_channel)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel_id)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    delall_handler = ConversationHandler(
        entry_points=[CommandHandler("delall", delete_all_channels)],
        states={2: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete_all)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_handler)
    app.add_handler(CommandHandler("del", delete_channel))
    app.add_handler(delall_handler)
    app.add_handler(CommandHandler("list", list_channels))
    app.add_handler(CommandHandler("help", help_command))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
