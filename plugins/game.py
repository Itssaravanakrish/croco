from time import time
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from words import choice
from mongo.users_and_chats import db
from utils import get_message, is_user_admin, update_user_score
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

async def new_game(client, message, language, game_mode: str, host_id: int) -> bool:
    try:
        if isinstance(game_mode, list):
            game_mode = game_mode[0]

        word = choice(game_mode)  
        logging.info(f"Selected word for game mode '{game_mode}': {word}")

        bot_info = await client.get_me()
        bot_id = bot_info.id

        # Check if the host is the bot itself
        if host_id == bot_id:
            logging.warning("The bot cannot be the host of the game.")
            return False

        # Retrieve the host's user information
        host_user = await client.get_users(host_id)

        game_data = {
            'start': time(),
            'host': {
                'id': host_id,
                'first_name': host_user.first_name,  # Use the host's first name
                'username': host_user.username,
            },
            'word': word,
            'game_mode': game_mode,
            'language': language.value
        }

        await db.set_game(message.chat.id, game_data)

        await message.reply_text(
            await get_message(language.value, "game_started", name=host_user.first_name, mode=game_mode, lang=language.value),  # Use host's name
            reply_markup=inline_keyboard_markup
        )
        return True
    except Exception as e:
        logging.error(f"Error in new_game: {e}")
        await message.reply_text(await get_message(language.value, "database_error"))
        return False

async def check_answer(client, message, game, language):
    current_word = game.get("word")
    host_id = game.get("host", {}).get("id")
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.text:
        if message.text.lower() == current_word.lower():
            winner_id = message.from_user.id
            winner_name = message.from_user.first_name

            if winner_id == int(host_id):
                await message.reply_sticker("CAACAgUAAyEFAASMPZdPAAEBWjVnnj1fEKVElmmYXzBc828kgDZTQQACNBQAAu9OkFSKgGFg2iVa2R4E")
                await message.reply_text(await get_message(language, "dont_tell_answer"))
            else:
                await update_user_score(chat_id, user_id, base_score=10, coins=5, xp=20)
                
                await message.reply_text(
                    await get_message(language, "correct_answer", winner=winner_name)
                )
                
                # Start a new game with the winner as the host
                await new_game(client, message, language, game.get("game_mode"), winner_id)  # Pass winner_id

@Client.on_message(filters.group & filters.command("game", CMD))
async def game_command(client, message):
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
        await message.reply_text(await get_message(language, "game_already_started"))
        return

    game_mode = await db.get_group_game_mode(chat_id)
    await new_game(client, message, language, game_mode, message.from_user.id)  # Pass host_id
    await message.reply_text(await get_message(language, "new_game_started"))

@Client.on_message(filters.group)
async def group_message_handler(client, message):
    chat_id = message.chat.id
    language_str = await db.get_chat_language(chat_id)
    
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN
        logging.warning(f"Invalid language string '{language_str}' in database for chat {chat_id}. Defaulting to EN.")

    game = await db.get_game(chat_id)

    if not game:
        return

    time_elapsed = time() - game['start']
    if time_elapsed >= GAME_TIMEOUT:
        await handle_end_game(client, message, language)
        return

    await check_answer(client, message, game, language)

@Client.on_callback_query(filters.regex("view|next|end_game"))
async def game_action_callback(client, callback_query):
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

    time_elapsed = time() - game['start']
    if time_elapsed >= GAME_TIMEOUT:
        await handle_end_game(client, callback_query.message, language)
        await callback_query.message.edit_text(await get_message(language, "game_timed_out"))
        return

    if callback_query.data == "view":
        word = game['word']
        await callback_query.answer(await get_message(language, "current_word", word=word), show_alert=True)

    elif callback_query.data == "next":
        try:
            game_mode = await db.get_group_game_mode(chat_id)
            if isinstance(game_mode, list) and game_mode:
                game_mode = game_mode[0]
            else:
                logging.warning(f"No valid game mode found for chat_id: {chat_id}. Defaulting to 'easy'.")
                game_mode = "easy"
                
            new_word = choice(game_mode)
            update_data = {"word": new_word}
            await db.update_game(chat_id, update_data)

            await callback_query.answer(await get_message(language, "new_word", word=new_word), show_alert=True)

        except Exception as e:
            logging.exception(f"Error updating word in database: {e}")
            await callback_query.answer(await get_message(language, "database_error"), show_alert=True)

    elif callback_query.data == "end_game":
        await handle_end_game(client, callback_query.message, language)
        await callback_query.message.delete()
        await client.send_message(chat_id, await get_message(language, "game_ended"))
        await callback_query.answer(await get_message(language, "game_ended_confirmation"), show_alert=True)

@Client.on_callback_query(filters.regex("choose_leader"))
async def choose_leader_callback(client, callback_query):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    try:
        game = await db.get_game(chat_id)
        if game:
            logging.warning(f"Game already ongoing for chat {chat_id}. Cannot choose a new leader.")
            await callback_query.answer("A game is already ongoing. Please end the game first.", show_alert=True)
            return

        game_mode = await db.get_group_game_mode(chat_id)
        if not game_mode:
            logging.warning(f"No game mode found for chat {chat_id}. Defaulting to 'easy'.")
            game_mode = "easy"
    except Exception as e:
        logging.error(f"Error retrieving game mode for chat {chat_id}: {e}")
        await callback_query.answer("Failed to retrieve game mode. Please try again.", show_alert=True)
        return

    try:
        # Set the clicked user as the host
        await new_game(client, callback_query.message, language, game_mode, user_id)  # Pass user_id
        await callback_query.answer(f"{callback_query.from_user.first_name} is now the leader! Starting the game...")
    except Exception as e:
        logging.error(f"Error starting new game for chat {chat_id}: {e}")
        await callback_query.answer("Failed to start the game. Please try again.", show_alert=True)

async def handle_end_game(client, message, language):
    try:
        await db.remove_game(message.chat.id)
        
        inline_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("I Want To Be A Leader 🙋‍♂️", callback_data="choose_leader")]]
        )
        
        await message.reply_text(
            await get_message(language, "choose_leader"),
            reply_markup=inline_keyboard
        )
    except Exception as e:
        logging.error(f"Error removing game from database: {e}")
        await message.reply_text(await get_message(language, "database_error"))
