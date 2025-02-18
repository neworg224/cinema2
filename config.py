import os
import logging
from logging.handlers import RotatingFileHandler

# Configs
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6816947603:AAGf2MkytwMll-Y3-QoMC8GT-rfouboFx2Y")
API_ID = int(os.environ.get("API_ID", "27298358"))
API_HASH = os.environ.get("API_HASH", "61f9df8d0892d91e166900b6674ea1e0")
OWNER_ID = int(os.environ.get("OWNER_ID", "6679174598"))
DB_URL = os.environ.get("DB_URL", "mongodb+srv://userbot:userbot@cluster0.yysgo8y.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "akhror")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002017650807"))
FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "-1002044482291"))
FORCE_SUB_CHANNEL_2 = int(os.environ.get("FORCE_SUB_CHANNEL_2", "-1002017090467"))  # Add your second channel ID here
FILE_AUTO_DELETE = int(os.getenv("FILE_AUTO_DELETE", "600")) # auto delete in seconds
PORT = os.environ.get("PORT", "8080")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

try:
    ADMINS=[6679174598]
    for x in (os.environ.get("ADMINS", "6679174598").split()):
        ADMINS.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")

# Add language options dictionary with organized groups
LANGUAGES = {
    'en': 'English 🇬🇧',
    'hi': 'हिंदी 🇮🇳',
    'es': 'Español 🇪🇸',
    'ru': 'Русский 🇷🇺',
    'uz': 'O\'zbek 🇺🇿',
    'ar': 'العربية 🇸🇦',
    'fr': 'Français 🇫🇷',
    'fa': 'فارسی 🇮🇷',
    'id': 'Indonesia 🇮🇩',
    'de': 'Deutsch 🇩🇪',
    'it': 'Italiano 🇮🇹',
    'tr': 'Türkçe 🇹🇷'
}

CUSTOM_CAPTION = """<b>📁 File Name:</b> <code>{filename}</code>

<b>📱 How to Play:</b>
• <b>Android:</b> Use VLC for Android
• <b>iPhone:</b> Use VLC for Mobile

<b>⚡️ Maintained By @acceptthyself</b>"""

PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False

DISABLE_CHANNEL_BUTTON = False

BOT_STATS_TEXT = "<b>BOT UPTIME :</b>\n{uptime}"

USER_REPLY_TEXT = "❌Don't Send Me Messages Directly I'm Only File Share Bot, use @cinemagic_hd_bot for movie searching🎬"

START_MSG = os.environ.get("START_MESSAGE", """Harry Potter all parts in one post (just click on title)

1) <a href="https://t.me/c/2044482291/216">Harry Potter and the Sorcerer's Stone</a>
2) <a href="https://t.me/c/2044482291/220">Harry Potter and the Chamber of Secrets</a>
3) <a href="https://t.me/c/2044482291/225">Harry Potter and the Prisoner of Azkaban</a>
4) <a href="https://t.me/c/2044482291/229">Harry Potter and the Goblet of Fire</a>
5) <a href="https://t.me/c/2044482291/235">Harry Potter and the Order of the Phoenix</a>
6) <a href="https://t.me/c/2044482291/237">Harry Potter and the Half-Blood Prince</a>
7) <a href="https://t.me/c/2044482291/246">Harry Potter and the Deathly Hallows: Part 1</a>
8) <a href="https://t.me/c/2044482291/251">Harry Potter and the Deathly Hallows: Part 2</a>

@cinemagic_hd - high-quality movies🎬""")

FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "Hi {mention}\n\n<b><i>You need to join our channel to download Harry Potter Movies\n\nKindly Join and click on /start again ☺️ </i></b>")

ADMINS.append(OWNER_ID)
ADMINS.append(6848088376)

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
