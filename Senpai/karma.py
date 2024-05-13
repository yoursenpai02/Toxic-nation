# <============================================== IMPORTS =========================================================>
from pyrogram.types import InlineKeyboardButton as ib
from telegram import InlineKeyboardButton

from Mikubot import BOT_USERNAME, OWNER_ID, SUPPORT_CHAT

# <============================================== CONSTANTS =========================================================>
START_IMG = [
    "https://graph.org/file/0127a4b43fd20f5b03eb6.jpg",
    "https://graph.org/file/18a995acbf326e3bb3df5.jpg",
    "https://graph.org/file/80930fad8add5f307910c.jpg",
    "https://graph.org/file/bac83d702ebfbffe38d1c.jpg",
    "https://graph.org/file/7a6fbcad400bad6ded0af.jpg",
    "https://graph.org/file/2923417b2a6feeed4fcb3.jpg",
    "https://graph.org/file/18a995acbf326e3bb3df5.jpg",
]

HEY_IMG = "https://graph.org/file/0127a4b43fd20f5b03eb6.jpg"

ALIVE_ANIMATION = [
    "https://telegra.ph/file/4e216093f28706310d3f5.mp4",
    "https://telegra.ph/file/6537d7191a01b9a665c8e.mp4",
    "https://telegra.ph/file/59b35f4240780cd0a6fcf.mp4",
    "https://telegra.ph/file/4e216093f28706310d3f5.mp4",
    "https://telegra.ph/file/6537d7191a01b9a665c8e.mp4",
    "https://telegra.ph/file/59b35f4240780cd0a6fcf.mp4",
    "https://telegra.ph/file/4e216093f28706310d3f5.mp4",
    "https://telegra.ph/file/6537d7191a01b9a665c8e.mp4",
]

FIRST_PART_TEXT = "✨ *ʜᴇʟʟᴏ* `{}` . . ."

PM_START_TEXT = "✨ *ɪ ᴀᴍ ʜᴀᴛꜱᴜɴᴇ ᴍɪᴋᴜ, ᴀ  ᴠɪʀᴛᴜᴀʟ ᴘᴏᴘ ꜱᴛᴀʀ ʀᴏʙᴏᴛ ᴡʜɪᴄʜ ᴄᴀɴ ʜᴇʟᴘ ʏᴏᴜ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴀɴᴅ ꜱᴇᴄᴜʀᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴡɪᴛʜ ʜᴜɢᴇ ɢʀᴏᴜᴘ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ*"

START_BTN = [
    [
        InlineKeyboardButton(
            text="⇦ ADD ME ⇨",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
    [
        InlineKeyboardButton(text="MANAGEMENT", callback_data="help_back"),
    ],
    [
        InlineKeyboardButton(text="DETAILS", callback_data="Miku_"),
        InlineKeyboardButton(text="AI", callback_data="ai_handler"),
        InlineKeyboardButton(text="MUSIC", callback_data="git_source"),
    ],
    [
        InlineKeyboardButton(text="CREATOR", url=f"tg://user?id={OWNER_ID}"),
    ],
]

GROUP_START_BTN = [
    [
        InlineKeyboardButton(
            text="⇦ ADD ME ⇨",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
    [
        InlineKeyboardButton(text="SUPPORT", url=f"https://t.me/{SUPPORT_CHAT}"),
        InlineKeyboardButton(text="CREATOR", url=f"tg://user?id={OWNER_ID}"),
    ],
]

ALIVE_BTN = [
    [
        ib(text="UPDATES", url="https://t.me/Hydra_Updates"),
        ib(text="SUPPORT", url="https://t.me/hydraXsupport"),
    ],
    [
        ib(
            text="⇦ ADD ME ⇨",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
]

HELP_STRINGS = """
🫧 *Hatsune-Miku* 🫧

☉ *Here, you will find a list of all the available commands.*

ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ : /
"""
