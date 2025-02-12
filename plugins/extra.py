import logging
import asyncio
from time import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from mongo.users_and_chats import db  # Import the database instance
from config import SUDO_USERS
from utils import get_message, register_user, register_chat
from words import choice  # Assuming words is a module that provides a choice function

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

    # Determine the user's preferred language (default to English)
    user_id = str(message.from_user.id)
    user_language = await db.get_user_language(user_id)  # Fetch the user's language preference from the database
    language = user_language if user_language in ["en", "ta", "hi"] else "en"  # Fallback to English if not set

    if ongoing_game:
        if (time() - ongoing_game['start']) >= GAME_TIMEOUT:
            await handle_end_game(client, message)
            await new_game(client, message, language)  # Start a new game
            return

        host_id = ongoing_game["host"]["id"]
        if message.from_user.id != host_id:
            await message.reply_text(get_message(language, "game_already_started"))  # Use the localized message
            return

        return

    await new_game(client, message, language)  # Start a new game

@Client.on_callback_query(filters.regex("start_new_game"))
async def start_new_game_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    # Determine the user's preferred language (default to English)
    user_id = str(callback_query.from_user.id)
    user_language = await db.get_user_language(user_id)  # Fetch the user's language preference from the database
    language = user_language if user_language in ["en", "ta", "hi"] else "en"  # Fallback to English if not set

    # Start a new game with the user who clicked the button as the host
    await new_game(client, callback_query.message, language=language)  # Pass the determined language

    # Retrieve the new game state to ensure it's set up correctly
    new_game_state = await db.get_game(callback_query.message.chat.id)

    if new_game_state:
        # Delete the old message to clean up
        await callback_query.message.delete()
        # Notify that a new game has started
        await client.send_message(
            callback_query.message.chat.id,
            get_message(language, "game_started", name=callback_query.from_user.first_name),  # Use the localized message
            reply_markup=inline_keyboard_markup  # Use your existing inline keyboard for the game
        )
        await callback_query.answer(get_message(language, "new_game_started"), show_alert=True)  # Notify the user
    else:
        await callback_query.answer(get_message(language, "failed_to_start_game"), show_alert=True)  # Notify failure

@Client.on_callback_query(filters.regex("end_game"))
async def end_now_callback(client: Client, callback_query: CallbackQuery):
    # Determine the user's preferred language (default to English)
    user_id = str(callback_query.from_user.id)
    user_language = await db.get_user_language(user_id)  # Fetch the user's language preference from the database
    language = user_language if user_language in ["en", "ta", "hi"] else "en"  # Fallback to English if not set

    game = await db.get_game(callback_query.message.chat.id)

    if game:
        if callback_query.from_user.id == game['host']['id']:
            await handle_end_game(client, callback_query.message)
            await callback_query.message.delete()
            await client.send_message(callback_query.message.chat.id, get_message(language, "game_ended"))  # Use the localized message
            await callback_query.answer(get_message(language, "game_ended_confirmation"), show_alert=True)  # Notify the user
        else:
            await callback_query.answer(get_message(language, "not_leader"), show_alert=True)  # Use the localized message
    else:
        await callback_query.answer(get_message(language, "no_game_ongoing"), show_alert=True)  # Use the localized message

@Client.on_message(filters.group & filters.command("end", CMD))
async def end_game_callback(client: Client, message: Message):
    # Determine the user's preferred language (default to English)
    user_id = str(message.from_user.id)
    user_language = await db.get_user_language(user_id)  # Fetch the user's language preference from the database
    language = user_language if user_language in ["en", "ta", "hi"] else "en"  # Fallback to English if not set

    game = await db.get_game(message.chat.id)
    if game:
        if game['host']['id'] == user_id:
            if await handle_end_game(client, message):
                await message.reply_text(get_message(language, "game_ended"))  # Use the localized message for game ended
            else:
                await message.reply_text(get_message(language, "error_ending_game"))  # Use the localized error message
        else:
            await message.reply_text(get_message(language, "not_host"))  # Use the localized message for not being the host
    else:
        await message.reply_text(get_message(language, "no_game_ongoing"))  # Use the localized message for no game ongoing

async def handle_end_game(client: Client, message: Message):
    # Logic to handle ending the game
    chat_id = message.chat.id
    await db.remove_game(chat_id) 
