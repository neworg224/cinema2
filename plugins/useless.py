from bot import Bot
from pyrogram.types import Message
from pyrogram import filters
from config import ADMINS, BOT_STATS_TEXT
from datetime import datetime
from helper_func import get_readable_time
from plugins.translations import get_translation, TRANSLATIONS


@Bot.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats(_,message: Message):
    bot_uptime = int(datetime.now().timestamp() - bot_start_time)
    uptime = get_readable_time(bot_uptime)
    await message.reply_text(BOT_STATS_TEXT.format(uptime))


@Bot.on_message(filters.private & filters.incoming)
async def useless(_, message: Message):
    # Get user's language code, default to 'en' if not set
    user_lang = message.from_user.language_code
    if user_lang:
        # Take only the first part of language code (e.g., 'en' from 'en-US')
        user_lang = user_lang.split('-')[0].lower()
        # Check if language exists in translations, if not fallback to English
        if user_lang not in TRANSLATIONS:
            user_lang = 'en'
    else:
        user_lang = 'en'
    
    # Get translated reply
    user_reply = get_translation('USER_REPLY_TEXT', user_lang)
    await message.reply(user_reply)


# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
