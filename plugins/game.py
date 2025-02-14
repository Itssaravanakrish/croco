from time import time
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from words import choice  # Assuming this module exists
from mongo.users_and_chats import db  # Assuming this module contains your database functions
from utils import get_message, is_user_admin  # Assuming this module exists

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

async def new_game(client: Client, message: Message, language="en", game_mode="easy") -> bool:
    word = choice(game_mode)

    bot_info = await client.get_me()
    bot_id = bot_info.id

    host_id = message.from_user.id
    if host_id == bot_id:
        return False

    try:
        await db.set_game(message.chat.id, {
            'start': time(),
            'host': {
                'id': host_id,
                'first_name': message.from_user.first_name,
                'username': message.from_user.username,
            },
            'word': word,
            'game_mode': game_mode
        })
    except Exception as e:
        logging.error(f"Error setting game in database: {e}")
        return False  # Indicate game creation failure

    await message.reply_text(
        await get_message(language, "game_started", name=message.from_user.first_name),
        reply_markup=inline_keyboard_markup
    )
    return True

@Client.on_message(filters.group & filters.command("game", CMD))
async def game_command(client: Client, message: Message):
    chat_id = message.chat.id # No need to convert to str
    try:
        ongoing_game = await db.get_game(chat_id)
    except Exception as e:
        logging.error(f"Error getting game from database: {e}")
        await message.reply_text(await get_message(await db.get_group_language(chat_id), "database_error"))
        return

    user_id = message.from_user.id # No need to convert to str
    language = await db.get_group_language(chat_id)
    game_mode = await db.get_group_game_mode(chat_id)

    if ongoing_game:
        if (time() - ongoing_game['start']) >= GAME_TIMEOUT:
            await handle_end_game(client, message, language) # Pass language here
            await new_game(client, message, language, game_mode)
            return

        host_id = ongoing_game["host"]["id"]
        if message.from_user.id != host_id:
            await message.reply_text(await get_message(language, "game_already_started"))
            return

    await new_game(client, message, language, game_mode)

@Client.on_callback_query(filters.regex("view|next|end_game"))
async def game_action_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    user_id = callback_query.from_user.id # No need to convert to str
    language = await db.get_group_language(callback_query.message.chat.id)

    try:
        game = await db.get_game(callback_query.message.chat.id)
    except Exception as e:
        logging.error(f"Error getting game from database: {e}")
        await callback_query.answer(await get_message(language, "database_error"), show_alert=True)
        return

    if not game:
        await callback_query.message.edit_text(await get_message(language, "no_game_ongoing"))
        return

    host_id = game['host']['id']

    if user_id != host_id:
        await callback_query.answer(await get_message(language, "not_leader"), show_alert=True)
        return

    if (time() - game['start']) >= GAME_TIMEOUT: # Check for timeout
        await handle_end_game(client, callback_query.message, language)
        await callback_query.message.edit_text(await get_message(language, "game_timed_out"))
        return

    if callback_query.data == "view":
        word = game['word']
        await callback_query.message.edit_text(await get_message(language, "current_word", word=word), reply_markup=inline_keyboard_markup)

    elif callback_query.data == "next":
        try:
            new_word = choice(game['game_mode'])
            result = await db.update_game(callback_query.message.chat.id, {"$set": {"word": new_word}}) # Atomic update
            if result.modified_count == 1:
                await callback_query.message.edit_text(await get_message(language, "new_word", word=new_word), reply_markup=inline_keyboard_markup)
            else:
                logging.error(f"Failed to update word (modified_count: {result.modified_count}) for chat {callback_query.message.chat.id}")
                await callback_query.answer(await get_message(language, "word_not_updated"), show_alert=True)
        except Exception as e:
            logging.error(f"Error updating word in database: {e}")
            await callback_query.answer(await get_message(language, "database_error"), show_alert=True)
            return

    elif callback_query.data == "end_game":
        if user_id == host_id:
            await handle_end_game(client, callback_query.message, language)
            await callback_query.message.delete()
            await client.send_message(callback_query.message.chat.id, await get_message(language, "game_ended"))
            await callback_query.answer(await get_message(language, "game_ended_confirmation"), show_alert=True)

@Client.on_message(filters.group & filters.command("set_mode", CMD))
async def set_game_mode(client: Client, message: Message):
    user_id = message.from_user.id # No need to convert to str
    language = await db.get_group_language(message.chat.id)

    if not await is_user_admin(client, message.chat.id, user_id):
        await message.reply_text(await get_message(language, "not_admin"))
        return

    mode = message.command[1] if len(message.command) > 1 else None
    if mode not in ["easy", "hard", "adult"]:
        await message.reply_text(await get_message(language, "invalid_mode"))
        return

    try:
        await db.set_group_game_mode(message.chat.id, mode)
        await message.reply_text(await get_message(language, "game_mode_set", mode=mode))
    except Exception as e:
        logging.error(f"Error setting game mode in database: {e}")
        await message.reply_text(await get_message(language, "database_error"))
        return

async def handle_end_game(client: Client, message: Message, language: str):
    try:
        await db.remove_game(message.chat.id)
        await message.reply_text(await get_message(language, "game_ended"))
    except Exception as e:
        logging.error(f"Error removing game from database: {e}")
        await message.reply_text(await get_message(language, "database_error"))
        return
