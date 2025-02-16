from time import time
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Sticker
from words import choice
from mongo.users_and_chats import db
from utils import get_message, is_user_admin
from script import Language

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

async def new_game(client: Client, message: Message, language: Language, game_mode="easy") -> bool:
    word = choice(game_mode)

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
        'language': language.value  # Store language as a STRING in the database - KEY CHANGE
    }

    try:
        await db.set_game(message.chat.id, game_data)
    except Exception as e:
        logging.error(f"Error setting game in database: {e}")
        await message.reply_text(await get_message(language.value, "database_error"))  # Use language.value
        return False

    # Retrieve game data and language from the database (if needed elsewhere):
    retrieved_game_data = await db.get_game(message.chat.id)  # Retrieve game data
    if retrieved_game_data:  # Check if game data exists
        retrieved_language_str = retrieved_game_data.get('language')  # Get language string from db
        try:
            retrieved_language = Language(retrieved_language_str)  # Convert back to Language enum
        except ValueError:
            retrieved_language = Language.EN  # Default if invalid
            logging.warning(f"Invalid language string '{retrieved_language_str}' in database for chat {message.chat.id}. Defaulting to EN.")
    else:
        retrieved_language = language # If no game data, use the language passed to the function

    await message.reply_text(
        await get_message(retrieved_language.value, "game_started", name=message.from_user.first_name, mode=game_mode),  # Use retrieved_language.value
        reply_markup=inline_keyboard_markup
    )
    return True

@Client.on_message(filters.group & filters.command("game", CMD))
async def game_command(client: Client, message: Message):
    chat_id = message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN
    game_mode = await db.get_group_game_mode(chat_id)

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
            await new_game(client, message, language, game_mode)
            return

        host_id = ongoing_game["host"]["id"]
        if message.from_user.id != host_id:
            await message.reply_text(await get_message(language, "game_already_started"))
            return

    await new_game(client, message, language, game_mode)

@Client.on_message(filters.group)
async def group_message_handler(client: Client, message: Message):
    chat_id = message.chat.id
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)  # Convert to enum, handle ValueError
    except ValueError:
        language = Language.EN  # Default to EN if invalid
        logging.warning(f"Invalid language string '{language_str}' in database for chat {message.chat.id}. Defaulting to EN.")

    game = await db.get_game(chat_id)

    if not game:
        return

    host_id = game.get("host", {}).get("id")
    current_word = game.get("word")

    if message.from_user.id == int(host_id) and message.text:
        if current_word and current_word.lower() in message.text.lower():
            await message.reply_sticker("CAACAgEAAx0CdytmQADK4wABb7Jj6h5w-f9p5l7k8l4AAj8MAAL58lVDKF-qY-F5j7AeBA")
            await message.reply_text(await get_message(language, "dont_tell_answer"))  # Use the enum!

    elif message.from_user.id != int(host_id) and current_word and message.text:
        if current_word.lower() == message.text.lower():
            winner_id = message.from_user.id
            winner_name = message.from_user.first_name

            await message.reply_text(await get_message(language, "correct_answer", winner=winner_name))  # Use the enum!

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
                await message.reply_text(await get_message(language, "database_error"))  # Use the enum!
                return

            new_game_message = await get_message(language, "new_game_started")  # Use the enum!
            await message.reply_text(new_game_message)

            try:
                host_user = await client.get_users(int(host_id))
                await client.send_message(int(host_id), await get_message(language, "game_ended_confirmation"))  # Use the enum!
            except Exception as e:
                logging.error(f"Error notifying previous host {host_id}: {e}")

@Client.on_callback_query(filters.regex("view|next|end_game"))
async def game_action_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

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

    if user_id != host_id:
        await callback_query.answer(await get_message(language, "not_leader"), show_alert=True)
        return

    time_elapsed = time() - game['start']
    if time_elapsed >= GAME_TIMEOUT:
        await handle_end_game(client, callback_query.message, language)
        await callback_query.message.edit_text(await get_message(language, "game_timed_out"))
        return

    if callback_query.data == "view":
        if user_id == host_id:  # Only answer if it's the host
            word = game['word']
            await callback_query.answer(await get_message(language, "current_word", word=word), show_alert=True) # Show the word in a popup for the host.
        else:
            await callback_query.answer(await get_message(language, "not_leader"), show_alert=True)  # Inform other users.

    elif callback_query.data == "next":
        if user_id == host_id:
            try:
                new_word = choice(game['game_mode'])
                result = await db.update_game(chat_id, {"$set": {"word": new_word}})
                if result.modified_count == 1:
                    await callback_query.answer(await get_message(language, "new_word", word=new_word), show_alert=True) # Show the new word in a popup for the host.
                else:
                    logging.error(f"Failed to update word (modified_count: {result.modified_count}) for chat {chat_id}")
                    await callback_query.answer(await get_message(language, "word_not_updated"), show_alert=True)
            except Exception as e:
                logging.error(f"Error updating word in database: {e}")
                await callback_query.answer(await get_message(language, "database_error"), show_alert=True)
                return
        else:
            await callback_query.answer(await get_message(language, "not_leader"), show_alert=True)

    elif callback_query.data == "end_game":
        if user_id == host_id:
            await handle_end_game(client, callback_query.message, language) # Pass enum
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
        return


async def handle_end_game(client: Client, message: Message, language: Language):  # Language as enum
    try:
        await db.remove_game(message.chat.id)
        await message.reply_text(await get_message(language, "game_ended"))  # Use enum
    except Exception as e:
        logging.error(f"Error removing game from database: {e}")
        await message.reply_text(await get_message(language, "database_error"))  # Use enum
        return
