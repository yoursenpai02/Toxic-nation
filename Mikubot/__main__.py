# <============================================== IMPORTS =========================================================>
import asyncio
import contextlib
import importlib
import json
import re
import time
import traceback
from platform import python_version
from random import choice

import psutil
import pyrogram
import telegram
import telethon
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import (
    BadRequest,
    ChatMigrated,
    Forbidden,
    NetworkError,
    TelegramError,
    TimedOut,
)
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown

import Database.sql.users_sql as sql
from Senpai.karma import *
from Mikubot import (
    BOT_NAME,
    LOGGER,
    OWNER_ID,
    SUPPORT_CHAT,
    TOKEN,
    StartTime,
    app,
    dispatcher,
    function,
    loop,
    tbot,
)
from Mikubot.plugins import ALL_MODULES
from Mikubot.plugins.helper_funcs.chat_status import is_user_admin
from Mikubot.plugins.helper_funcs.misc import paginate_modules

# <=======================================================================================================>

PYTHON_VERSION = python_version()
PTB_VERSION = telegram.__version__
PYROGRAM_VERSION = pyrogram.__version__
TELETHON_VERSION = telethon.__version__


# <============================================== FUNCTIONS =========================================================>
async def ai_handler_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "ai_handler":
        await query.answer()
        await query.message.edit_text(
            "🧠 *Artificial Intelligence Functions*:\n\n"
            "All Commands:\n"
            "➽ /askgpt <write query>: A chatbot using GPT for responding to user queries.\n\n"
            "➽ /palm <write prompt>: Performs a Palm search using a chatbot.\n\n"
            "➽ /upscale <reply to image>: Upscales your image quality.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "𝙈𝙊𝙍𝙀 𝙄𝙈𝘼𝙂𝙀 𝙂𝙀𝙉 ➪", callback_data="more_ai_handler"
                        ),
                    ],
                    [
                        InlineKeyboardButton("» 𝙃𝙊𝙈𝙀 «", callback_data="Miku_back"),
                    ],
                ],
            ),
        )


async def more_ai_handler_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "more_ai_handler":
        await query.answer()
        await query.message.edit_text(
            "*Here's more image gen-related commands*:\n\n"
            "Command: /meinamix\n"
            "  • Description: Generates an image using the meinamix model.\n\n"
            "Command: /darksushi\n"
            "  • Description: Generates an image using the darksushi model.\n\n"
            "Command: /meinahentai\n"
            "  • Description: Generates an image using the meinahentai model.\n\n"
            "Command: /darksushimix\n"
            "  • Description: Generates an image using the darksushimix model.\n\n"
            "Command: /anylora\n"
            "  • Description: Generates an image using the anylora model.\n\n"
            "Command: /cetsumix\n"
            "  • Description: Generates an image using the cetus-mix model.\n\n"
            "Command: /darkv2\n"
            "  • Description: Generates an image using the darkv2 model.\n\n"
            "Command: /creative\n"
            "  • Description: Generates an image using the creative model.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="ai_handler"),
                    ],
                ],
            ),
        )


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Mikubot.plugins." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
async def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    await dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    message = update.effective_message
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                await send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                await send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="◁", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower() == "markdownhelp":
                IMPORTED["exᴛʀᴀs"].markdown_help_sender(update)
            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                await IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            lol = await message.reply_photo(
                photo=str(choice(START_IMG)),
                caption=FIRST_PART_TEXT.format(escape_markdown(first_name)),
                parse_mode=ParseMode.MARKDOWN,
            )
            await asyncio.sleep(0.2)
            guu = await update.effective_message.reply_text("🐾")
            await asyncio.sleep(1.8)
            await guu.delete()  # Await this line
            await update.effective_message.reply_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(START_BTN),
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=False,
            )
    else:
        await message.reply_photo(
            photo=str(choice(START_IMG)),
            reply_markup=InlineKeyboardMarkup(GROUP_START_BTN),
            caption="<b>I am Alive!</b>\n\n<b>Since​:</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    await context.bot.send_message(
        chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML
    )


# for test purposes
async def error_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    try:
        raise error
    except Forbidden:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "➲ *HELP SECTION OF* *{}* :\n".format(HELPABLE[module].__mod_name__)
                + HELPABLE[module].__help__
            )
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="◁", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        await context.bot.answer_callback_query(query.id)

    except BadRequest:
        pass


async def stats_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "insider_":
        uptime = get_readable_time((time.time() - StartTime))
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        text = f"""
𝙎𝙮𝙨𝙩𝙚𝙢 𝙨𝙩𝙖𝙩𝙨@𝙃𝙖𝙩𝙨𝙪𝙣𝙚_𝙈𝙞𝙠𝙪_𝙍𝙤𝙗𝙤𝙩
➖➖➖➖➖➖
UPTIME ➼ {uptime}
CPU ➼ {cpu}%
RAM ➼ {mem}%
DISK ➼ {disk}%

PYTHON ➼ {PYTHON_VERSION}

PTB ➼ {PTB_VERSION}
TELETHON ➼ {TELETHON_VERSION}
PYROGRAM ➼ {PYROGRAM_VERSION}
"""
        await query.answer(text=text, show_alert=True)


async def gitsource_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "git_source":
        await query.answer()
        await query.message.edit_text(
            " *ʜᴇʀᴇ ɪꜱ ʜᴇʟᴘ ᴍᴇɴᴜ ꜰᴏʀ ᴍᴜꜱɪᴄ*\n\n",
            
        
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(" admin ", callback_data="music_admin"),
            InlineKeyboardButton(" auth ", callback_data="music_auth"),
            InlineKeyboardButton(" broadcast ", callback_data="music_broadcast"),
        ],
        [
            InlineKeyboardButton(" Bl-chat ", callback_data="music_blchat"),
            InlineKeyboardButton(" Bl-user ", callback_data="music_bluser"),
            InlineKeyboardButton(" cplay ", callback_data="music_cplay"),
        ],
        [
            InlineKeyboardButton(" gban ", callback_data="music_gban"),
            InlineKeyboardButton(" loop ", callback_data="music_loop"),
            InlineKeyboardButton(" maintenance ", callback_data="music_maintenance"),
        ],
        [
            InlineKeyboardButton(" ping ", callback_data="music_ping"),
            InlineKeyboardButton(" play ", callback_data="music_play"),
            InlineKeyboardButton(" shuffle ", callback_data="music_shuffle"),
        ],
        [
            InlineKeyboardButton(" seek ", callback_data="music_seek"),
            InlineKeyboardButton(" song ", callback_data="music_song"),
            InlineKeyboardButton(" speed ", callback_data="music_speed"),
        ],
                    [
                        InlineKeyboardButton("» 𝙃𝙊𝙈𝙀 «", callback_data="Miku_back"),
                    ],
                ],
            ),
        )


async def music_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_admin":
        await query.answer()
        await query.message.edit_text(
            "*Here's ADMIN related commands*:\n\n"
            "  • just add C in the starting of the commands to use them for channel.\n\n"
            "Command: /pause\n"
            "  • Description: Pause the current playing stream.\n\n"
            "Command: /resume\n"
            "  • Description: Resume the pause stream.\n\n"
            "Command: /skip\n"
            "  • Description: Skip the current playing stream\n"
            " and start streaming the next track in the\n"
            " queue.\n\n"
            "Command: /end or /stop\n"
            "  • Description: Clear the queue and end\n"
            " the current playing stream.\n\n"
            "Command: /player\n"
            "  • Description: Get a interactive player panel.\n\n"
            "Command: /queue\n"
            "  • Description: Show the queued track list.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_play":
        await query.answer()
        await query.message.edit_text(
            "*Here's Play commands*:\n\n"
            "Command: /play or /vplay or /cplay\n"
            "  • Description: Bot will start playing your given query on voice chat or stream live links on voice chat.\n\n"
            "Command: /playforce or /vplayforce or /cplayforce\n"
            "  • Description: Force play stop the current playing track on voice chat and start playing the searched track instantly without disturbing/clearing queue.\n\n"
            "Command: /channelplay\n"
            "  • Description: chat username or id or disable - connect channel to a group and stream music on channel voice chat from your group.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_broadcast":
        await query.answer()
        await query.message.edit_text(
            "*Here's BROADCAST FEATURES [only for sudoers]*:\n\n"
            "Command: /broadcast\n"
            "  • Description: Broadcast a message to served chats of the bot.\n\n"
            "Broadcasting modes\n"
            "Command: -pin\n"
            "  • Description: Pin your broadcasted messages in served chats.\n\n"
            "Command: -pinloud\n"
            "  • Description: Pin your broadcasted messages in served chats and send notification to the members.\n\n"
            "Command: -user\n"
            "  • Description: Broadcast the message to the users who have started your bot.\n\n"
            "Command: -assistant\n"
            "  • Description: Broadcast your message from assistant account of the bot.\n\n"
            "Command: -nobot\n"
            "  • Description: Forces the bot to not broadcast the message.\n\n"
            "EXAMPLE: /broadcast -user -assistant -pin testing broadcast.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_blchat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_blchat":
        await query.answer()
        await query.message.edit_text(
            "*Here's CHAT BLACKLIST FEATURES: [only for sedoers]*:\n\n"
            "Restrict shit chats to use our precious bot.\n\n"
            "Command: /blacklistchat\n"
            "  • Description: Blacklist a chat from using the bot.\n\n"
            "Command: /whitelistchat\n"
            "  • Description: Whitelist a chat from using the bot.\n\n"
            "Command: /blacklistedchat\n"
            "  • Description: show to list of blacklisted chats.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )
async def music_bluser_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_bluser":
        await query.answer()
        await query.message.edit_text(
            "*Here's BLOCK USERS [only for sudoers]*:\n\n"
            "Starts ignoring the blacklisted user, so that he/she can't use the bot commands.\n\n"
            "Command: /block\n"
            "  • Description: Block the user from our bot.\n\n"
            "Command: /unblock\n"
            "  • Description: unblocks the blocked user.\n\n"
            "Command: /blockedusers\n"
            "  • Description: Show the list of blocked users.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_cplay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_cplay":
        await query.answer()
        await query.message.edit_text(
            "*Here's CHANNEL PLAY commands*:\n\n"
            "You can stream audio/video in channel.\n\n"
            "Command: /cplay\n"
            "  • Description: Starts streaming the requested audio track on the channel's videochat.\n\n"
            "Command: /cvplay\n"
            "  • Description: Starts streaming the requested vudeo track on the channel's videochat.\n\n"
            "Command: /cplayforce or /cvplayforce\n"
            "  • Description: Stops the ongoing stream and starts streaming the requested track.\n\n"
            "Command: /channelplay\n"
            "  • Description: connect channel to a group and start ls streaming tracks by the help of commands sent in group. \n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_gban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_gban":
        await query.answer()
        await query.message.edit_text(
            "*Here's GLOBAL BAN FEATURES [only for sudoers]*:\n\n"
            "Command: /gban\n"
            "  • Description: Globally bans the chutiya from all the served chats and blacklist him from using the bot.\n\n"
            "Command: /ungban\n"
            "  • Description: Globally unban the globally banned user.\n\n"
            "Command: /gbannedusers\n"
            "  • Description: Show the list of globally banned users.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_loop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_loop":
        await query.answer()
        await query.message.edit_text(
            "*Here's LOOP STREAM commands*:\n\n"
            "Starts streaming the ongoing stream in loop.\n\n"
            "Command: /loop\n"
            "  • Description: Enables/disables loop for ongoing stream.\n\n"
            "Command: /loop\n"
            "  • Description: Enables the loop for the guven value.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_maintenance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_maintenance":
        await query.answer()
        await query.message.edit_text(
            "*Here's MAINTENANCE MODE [only for sudoers]*:\n\n"
            "Command: /logs\n"
            "  • Description: Get logs of the bot.\n\n"
            "Command: /logger\n"
            "  • Description: Bot will start logging the activities happen on bot.\n\n"
            "Command: /maintenance\n"
            "  • Description: Enable or disable the maintenance mode of your bot.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_ping_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_ping":
        await query.answer()
        await query.message.edit_text(
            "*Here's PING & STATS commands*:\n\n"
            "Command: /mstart\n"
            "  • Description: Starts the music bot.\n\n"
            "Command: /mhelp\n"
            "  • Description: Get help menu with explanation of commands.\n\n"
            "Command: /ping\n"
            "  • Description: show the ping and system stats of the bot.\n\n"
            "Command: /stats\n"
            "  • Description: Showa the overall stats of the bot.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_auth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_auth":
        await query.answer()
        await query.message.edit_text(
            "*Here's AUTH USERS commands*:\n\n"
            "*Auth users can use admin rights in the bot without admin rights in the chat.*:\n"
            "Command: /auth\n"
            "  • Description: Add user to auth list of the bot.\n\n"
            "Command: /unauth\n"
            "  • Description: Remove auth users from the auth users list.\n\n"
            "Command: /authusers\n"
            "  • Description: Show the list of auth users of the group.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_shuffle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_shuffle":
        await query.answer()
        await query.message.edit_text(
            "*Here's SHUFFLE QUEUE commands*:\n\n"
            "Command: /shuffle\n"
            "  • Description: Shuffle's the queue.\n\n"
            "Command: /queue\n"
            "  • Description: Shows the shuffled queue.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_seek_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_seek":
        await query.answer()
        await query.message.edit_text(
            "*Here's SEEK STREAM commands*:\n\n"
            "Command: /seek\n"
            "  • Description: seek the stream to the given duration.\n\n"
            "Command: /seekback\n"
            "  • Description: backward seek the stream to the guven duration.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_song_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_song":
        await query.answer()
        await query.message.edit_text(
            "*Here's SONG DOWNLOAD  commands*:\n\n"
            "Command: /song\n"
            "  • Description: Download any track from YouTube in mp3 or mp4 formats.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def music_speed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "music_speed":
        await query.answer()
        await query.message.edit_text(
            "*Here's SPEED commands*:\n\n"
            "You can control the playback speed of the ongoing stream.[admins only]\n\n"
            "Command: /speed or /playback\n"
            "  • Description: Gor adjusting the audio playback speed in group.\n\n"
            "Command: /cspeed or /cplayback\n"
            "  • Description: For adjusting the audio playback speed in channel.\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ 𝘽𝘼𝘾𝙆", callback_data="git_source"),
                    ],
                ],
            ),
        )

async def repo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    source_link = "hello"
    message_text = f"*Here is the link for the public source repo*:\n\n{source_link}"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False,
    )


async def Miku_about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "Miku_":
        uptime = get_readable_time((time.time() - StartTime))
        message_text = (
            f"➲ <b>Ai integration.</b>"
            f"\n➲ <b>Advance management capability.</b>"
            f"\n➲ <b>Anime bot functionality.</b>"
            f"\n\n<b>USERS</b> » {sql.num_users()}"
            f"\n<b>CHATS</b> » {sql.num_chats()}"
            f"\n\n<b>Click on the buttons below for getting help and info about</b> {BOT_NAME}."
        )
        await query.message.edit_text(
            text=message_text,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ABOUT", callback_data="Miku_support"
                        ),
                        InlineKeyboardButton(text="COMMAND", callback_data="help_back"),
                    ],
                    [
                        InlineKeyboardButton(text="INSIDER", callback_data="insider_"),
                    ],
                    [
                        InlineKeyboardButton(text="◁", callback_data="Miku_back"),
                    ],
                ]
            ),
        )
    elif query.data == "Miku_support":
        message_text = (
            "*Our bot leverages SQL, MongoDB, Telegram, MTProto for secure and efficient operations. It resides on a high-speed server, integrates numerous APIs, ensuring quick and versatile responses to user queries.*"
            f"\n\n*If you find any bug in {BOT_NAME} Please report it at the support chat.*"
        )
        await query.message.edit_text(
            text=message_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="SUPPORT", url=f"https://t.me/{SUPPORT_CHAT}"
                        ),
                        InlineKeyboardButton(
                            text="DEVELOPER", url=f"tg://user?id={OWNER_ID}"
                        ),
                    ],
                    [
                        InlineKeyboardButton(text="◁", callback_data="Miku_"),
                    ],
                ]
            ),
        )
    elif query.data == "Miku_back":
        first_name = update.effective_user.first_name
        await query.message.edit_text(
            PM_START_TEXT.format(escape_markdown(first_name), BOT_NAME),
            reply_markup=InlineKeyboardMarkup(START_BTN),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )


async def get_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            await update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="HELP",
                                url="https://t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        await update.effective_message.reply_text(
            "» Choose an option for getting help.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="OPEN IN PM",
                            url="https://t.me/{}?start=help".format(
                                context.bot.username
                            ),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="OPEN HERE",
                            callback_data="help_back",
                        )
                    ],
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        await send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="◁", callback_data="help_back")]]
            ),
        )

    else:
        await send_help(chat.id, HELP_STRINGS)


async def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            await dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            await dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            await dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            await dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


async def settings_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            await query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="◁",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            await query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            await query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            await query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        await query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


async def get_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            await msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="SETTINGS",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        await send_settings(chat.id, user.id, True)


async def migrate_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, ᴛᴏ %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        with contextlib.suppress(KeyError, AttributeError):
            mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully Migrated!")
    raise ApplicationHandlerStop


# <=======================================================================================================>


# <=================================================== MAIN ====================================================>
def main():
    function(CommandHandler("start", start))

    function(CommandHandler("help", get_help))
    function(CallbackQueryHandler(help_button, pattern=r"help_.*"))

    function(CommandHandler("settings", get_settings))
    function(CallbackQueryHandler(settings_button, pattern=r"stngs_"))
    function(CommandHandler("repo", repo))
    function(CallbackQueryHandler(gitsource_callback, pattern=r"git_source"))
    function(CallbackQueryHandler(Miku_about_callback, pattern=r"Miku_"))
    function(CallbackQueryHandler(music_admin_callback, pattern=r"music_admin"))
    function(CallbackQueryHandler(music_auth_callback, pattern=r"music_auth"))
    function(CallbackQueryHandler(music_broadcast_callback, pattern=r"music_broadcast"))
    function(CallbackQueryHandler(music_blchat_callback, pattern=r"music_blchat"))
    function(CallbackQueryHandler(stats_back, pattern=r"insider_"))
    function(CallbackQueryHandler(music_bluser_callback, pattern=r"music_bluser"))
    function(CallbackQueryHandler(music_cplay_callback, pattern=r"music_cplay"))
    function(CallbackQueryHandler(music_gban_callback, pattern=r"music_gban"))
    function(CallbackQueryHandler(music_loop_callback, pattern=r"music_loop"))
    function(CallbackQueryHandler(music_maintenance_callback, pattern=r"music_maintenance"))
    function(CallbackQueryHandler(music_ping_callback, pattern=r"music_ping"))
    function(CallbackQueryHandler(music_play_callback, pattern=r"music_play"))
    function(CallbackQueryHandler(music_shuffle_callback, pattern=r"music_shuffle"))
    function(CallbackQueryHandler(music_seek_callback, pattern=r"music_seek"))
    function(CallbackQueryHandler(music_song_callback, pattern=r"music_song"))
    function(CallbackQueryHandler(music_speed_callback, pattern=r"music_speed"))
    function(CallbackQueryHandler(ai_handler_callback, pattern=r"ai_handler"))
    function(CallbackQueryHandler(more_ai_handler_callback, pattern=r"more_ai_handler"))
    function(MessageHandler(filters.StatusUpdate.MIGRATE, migrate_chats))

    dispatcher.add_error_handler(error_callback)

    LOGGER.info("Mikubot is starting >> Using long polling.")
    dispatcher.run_polling(timeout=15, drop_pending_updates=True)


if __name__ == "__main__":
    try:
        LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
        tbot.start(bot_token=TOKEN)
        app.start()
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        err = traceback.format_exc()
        LOGGER.info(err)
    finally:
        try:
            if loop.is_running():
                loop.stop()
        finally:
            loop.close()
        LOGGER.info(
            "------------------------ Stopped Services ------------------------"
        )
# <==================================================== END ===================================================>
