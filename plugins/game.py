from time import time
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from words import choice
from mongo.users_and_chats import db
from script import messages_en, messages_ta, messages_hi  # Import messages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

CMD = ["/", "."]
GAME_TIMEOUT = 300  # Timeout duration in seconds

# Inline keyboard for the game
inline_keyboard_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ꜱᴇᴇ ᴡᴏʀᴅ 👀", callback_data="view"),
         InlineKeyboardButton("ɴᴇxᴛ ᴡᴏʀᴅ 🔄", callback_data="next")],
        [InlineKeyboardButton("ɪ ᴅᴏɴ'ᴛ ᴡᴀɴᴛ ᴏ ʙᴇ ᴀ ʟᴇᴀᴅᴇʀ🙅‍♂", callback_data="end_game")]
    ]
)

# Inline keyboard for when the user opts to become a leader
want_to_be_leader_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("ɪ ᴡᴀɴᴛ Tᴏ ʙᴇ ᴀ ʟᴇᴀᴅᴇʀ🙋‍♂", callback_data="start_new_game")]
    ]
)

async def get_message(language, key, **kwargs):
    if language == "en":
        return messages_en[key].format(**kwargs)
    elif language == "ta":
        return messages_ta[key].format(**kwargs)
    elif language == "hi":
        return messages_hi[key].format(**kwargs)

async def new_game(client: Client, message: Message, language="en") -> bool:
    word = choice()  # Get a new word for the game

    # Get the bot's ID
    bot_info = await client.get_me()
    bot_id = bot_info.id

    # Ensure the host is not the bot
    host_id = message.from_user.id
    if host_id == bot_id:
        return False  # Prevent the bot from being set as the host

    await db.set_game(message.chat.id, {
        'start': time(),
        'host': {
            'id': host_id,
            'first_name': message.from_user.first_name,
            'username': message.from_user.username,
        },
        'word': word,
    })
    await message.reply_text(get_message(language, "game_started", name=message.from_user.first_name), reply_markup=inline_keyboard_markup)
    return True

@Client.on_message(filters.group & filters.command("game", CMD))
async def game_command(client: Client, message: Message):
    chat_id = str(message.chat.id)
    ongoing_game = await db.get_game(chat_id)

    if ongoing_game:
        if (time() - ongoing_game['start']) >= GAME_TIMEOUT:
            await handle_end_game(client, message)
            await new_game(client, message)  # Start a new game
            return

        host_id = ongoing_game["host"]["id"]
        if message.from_user.id != host_id:
            await message.reply_text(get_message("en", "game_already_started"))  # Change "en" to the desired language
            return

        return

    await new_game(client, message)  # Start a new game

@Client.on_message(filters.group & filters.command("settings", CMD))
async def settings_command(client: Client, message: Message):
    await message.reply_text(get_message("en", "settings_option"))  # Change "en" to the desired language

@Client.on_callback_query(filters.regex("start_new_game"))
async def start_new_game_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await new_game(client, callback_query.message, language="en")  # Change "en" to the desired language

@Client.on_callback_query(filters.regex("end_game"))
async def end_now_callback(client: Client, callback_query: CallbackQuery):
    game = await db.get_game(callback_query.message.chat.id)

    if game:
        if callback_query.from_user.id == game['host']['id']:
            await handle_end_game(client, callback_query.message)
            await callback_query.message.delete()
            await client.send_message(callback_query.message.chat.id, get_message("en", "game_already_started"))  # Change "en" to the desired language
            await callback_query.answer("The game has been ended.", show_alert=True)
        else:
            await callback_query.answer("You are not the leader. You cannot end the game.", show_alert=True)
    else:
        await callback_query.answer("The game is already ended.", show_alert=True)

@Client.on_message(filters.group & filters.command("end", CMD))
async def end_game_callback(client: Client, message: Message):
    game = await db.get_game(message.chat.id)
    if game:
        if game['host']['id'] == message.from_user.id:
            if await handle_end_game(client, message):
                await message.reply_text(get_message("en", "game_already_started"))  # Change "en" to the desired language
            else:
                await message.reply_text("An error occurred while trying to end the game. Please try again.")
        else:
            await message.reply_text("You are not the host or there is no game to end.")
    else:
        await message.reply_text("There is no game ongoing to end.")
