#game.py

from time import time
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from words import choice
from mongo.users_and_chats import db
from utils import get_message, is_user_admin
from script import Language

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

CMD = ["/", "."]
GAME_TIMEOUT = 300

inline_keyboard_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("See Word 👀", callback_data="view"),
         InlineKeyboardButton("Next Word 🔄", callback_data="next")],
        [InlineKeyboardButton("I Don't Want To Be A Leader 🙅‍♂️", callback_data="end_game")]
    ]
)

async def new_game(client: Client, message: Message, language: Language, game_mode: str) -> bool:
    try:
        word = choice(game_mode)  # Get a word based on the game mode

        bot_info = await client.get_me()
        bot_id = bot_info.id

        host_id = message.from_user.id
        if host_id == bot_id:
            return False

        game_data = {
            'start': time(),
            'host': {
                'id': host_id,
                'first_name': message.from_user.first_name,
                'username': message.from_user.username,
            },
            'word': word,
            'game_mode': game_mode,
            'language': language.value
        }

        await db.set_game(message.chat.id, game_data)

        await message.reply_text(
            await get_message(language.value, "game_started", name=message.from_user.first_name, mode=game_mode, lang=language.value),
            reply_markup=inline_keyboard_markup
        )
        return True
    except Exception as e:
        logging.error(f"Error in new_game: {e}")
        await message.reply_text(await get_message(language.value, "database_error"))
        return False

@Client.on_message(filters.group & filters.command("game", CMD))
async def game_command(client: Client, message: Message):
    chat_id = message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    try:
        ongoing_game = await db.get_game(chat_id)
    except Exception as e:
        logging.error(f"Error getting game from database: {e}")
        await message.reply_text(await get_message(language, "database_error"))
        return

    if ongoing_game:
        time_elapsed = time() - ongoing_game['start']
        if time_elapsed >= GAME_TIMEOUT:
            await handle_end_game(client, message, language)
            game_mode = await db.get_group_game_mode(chat_id)  # Get the game mode
            await new_game(client, message, language, game_mode)  # Pass game_mode
            return

        host_id = ongoing_game["host"]["id"]
        if message.from_user.id != host_id:
            await message.reply_text(await get_message(language, "game_already_started"))
            return

    game_mode = await db.get_group_game_mode(chat_id)  # Get the game mode
    await new_game(client, message, language, game_mode)  # Pass game_mode

@Client.on_message(filters.group)
async def group_message_handler(client: Client, message: Message):
    chat_id = message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN
        logging.warning(f"Invalid language string '{language_str}' in database for chat {message.chat.id}. Defaulting to EN.")

    game = await db.get_game(chat_id)

    if not game:
        return

    host_id = game.get("host", {}).get("id")
    current_word = game.get("word")

    if message.from_user.id == int(host_id) and message.text:
        if current_word and current_word.lower().strip() in message.text.lower().strip():
            await message.reply_sticker("CAACAgEAAx0CdytmQADK4wABb7Jj6h5w-f9p5l7k8l4AAj8MAAL58lVDKF-qY-F5j7AeBA")
            await message.reply_text(await get_message(language, "dont_tell_answer"))

    elif message.from_user.id != int(host_id) and current_word and message.text:
        if current_word.lower().strip() == message.text.lower().strip():
            winner_id = message.from_user.id
            winner_name = message.from_user.first_name

            await message.reply_text(await get_message(language, "correct_answer", winner=winner_name))

            new_word = choice(game.get("game_mode"))
            new_game_data = {
                'start': time(),
                'host': {'id': str(winner_id), 'first_name': winner_name, 'username': message.from_user.username},
                'word': new_word,
                'game_mode': game.get("game_mode")
            }
            try:
                await db.set_game(chat_id, new_game_data)
            except Exception as e:
                logging.error(f"Error setting game in database: {e}")
                await message.reply_text(await get_message(language, "database_error"))
                return

            await message.reply_text(
                await get_message(language, "new_game_started", name=winner_name, word=new_word),
                reply_markup=inline_keyboard_markup
            )

@Client.on_callback_query(filters.regex("view|next|end_game"))
async def game_action_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Get the language for the chat
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    # Retrieve the current game state
    try:
        game = await db.get_game(chat_id)
    except Exception as e:
        logging.error(f"Error getting game from database: {e}")
        await callback_query.answer(await get_message(language, "database_error"), show_alert=True)
        return

    if not game:
        await callback_query.message.edit_text(await get_message(language, "no_game_ongoing"))
        return

    host_id = game['host']['id']

    # Check if the user is the host
    if user_id != host_id:
        await callback_query.answer(await get_message(language, "not_leader"), show_alert=True)
        return

    # Check for game timeout
    time_elapsed = time() - game['start']
    if time_elapsed >= GAME_TIMEOUT:
        await handle_end_game(client, callback_query.message, language)
        await callback_query.message.edit_text(await get_message(language, "game_timed_out"))
        return

    # Handle the "view" action
    if callback_query.data == "view":
        word = game['word']
        await callback_query.answer(await get_message(language, "current_word", word=word), show_alert=True)

    # Handle the "next" action
    elif callback_query.data == "next":
        try:
            game_mode = await db.get_group_game_mode(chat_id)  # Get the game modes as a LIST
            new_word = choice(game_mode)  # Use the LIST for choice()
            update_data = {"$set": {"word": new_word}}  # Update with the new word
            await db.update_game(chat_id, update_data)

            await callback_query.answer(await get_message(language, "new_word", word=new_word), show_alert=True)

        except Exception as e:
            logging.exception(f"Error updating word in database: {e}")
            await callback_query.answer(await get_message(language, "database_error"), show_alert=True)

    # Handle the "end_game" action
    elif callback_query.data == "end_game":
        await handle_end_game(client, callback_query.message, language)
        await callback_query.message.delete()
        await client.send_message(chat_id, await get_message(language, "game_ended"))
        await callback_query.answer(await get_message(language, "game_ended_confirmation"), show_alert=True)


@Client.on_message(filters.group & filters.command("set_mode", CMD))
async def set_game_mode(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    if not await is_user_admin(client, chat_id, user_id):
        await message.reply_text(await get_message(language, "not_admin"))
        return

    mode = message.command[1] if len(message.command) > 1 else None
    if mode not in ["easy", "hard", "adult"]:
        await message.reply_text(await get_message(language, "invalid_mode"))
        return

    try:
        await db.set_group_game_mode(chat_id, mode)
        await message.reply_text(await get_message(language, "game_mode_set", mode=mode))
    except Exception as e:
        logging.error(f"Error setting game mode in database: {e}")
        await message.reply_text(await get_message(language, "database_error"))


async def handle_end_game(client: Client, message: Message, language: Language):
    try:
        await db.remove_game(message.chat.id)
        await message.reply_text(await get_message(language, "game_ended"))  # Use enum
    except Exception as e:
        logging.error(f"Error removing game from database: {e}")
        await message.reply_text(await get_message(language, "database_error"))  # Use enum
