from time import time
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Sticker
from words import choice
from mongo.users_and_chats import db
from utils import get_message, is_user_admin
from script import Language # Import Language enum

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
        [InlineKeyboardButton("See Word 👀", callback_data="view"),
         InlineKeyboardButton("Next Word 🔄", callback_data="next")],
        [InlineKeyboardButton("I Don't Want To Be A Leader 🙅‍♂️", callback_data="end_game")]
    ]
)

async def new_game(client: Client, message: Message, language_str="en", game_mode="easy") -> bool:  # Language as string
    try:
        language = Language(language_str)  # Convert to enum
    except ValueError:
        language = Language.EN  # Default to EN

    word = choice(game_mode)

    bot_info = await client.get_me()
    bot_id = bot_info.id

    host_id = message.from_user.id
    if host_id == bot_id:
        return False

    game_data = {  # Store game data in a dictionary for clarity
        'start': time(),
        'host': {
            'id': host_id,
            'first_name': message.from_user.first_name,
            'username': message.from_user.username,
        },
        'word': word,
        'game_mode': game_mode
    }

    try:
        await db.set_game(message.chat.id, game_data)
    except Exception as e:
        logging.error(f"Error setting game in database: {e}")
        await message.reply_text(await get_message(language, "database_error"))  # Notify user of database error
        return False

    await message.reply_text(
        await get_message(language, "game_started", name=message.from_user.first_name, mode=game_mode, lang=language_str),  # Pass mode and lang!
        reply_markup=inline_keyboard_markup
    )
    return True

@Client.on_message(filters.group & filters.command("game", CMD))
async def game_command(client: Client, message: Message):
    chat_id = message.chat.id
    language_str = await db.get_chat_language(chat_id)  # Get as string
    try:
        language = Language(language_str)  # Convert to enum
    except ValueError:
        language = Language.EN  # Default to EN
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
            await handle_end_game(client, message, language_str)  # End the old game (pass string)
            await new_game(client, message, language_str, game_mode)  # Start a new game (pass string)
            return

        host_id = ongoing_game["host"]["id"]
        if message.from_user.id != host_id:
            await message.reply_text(await get_message(language, "game_already_started"))
            return

    await new_game(client, message, language_str, game_mode)  # Start a new game (pass string)
    
@Client.on_message(filters.group)  # Filter all group messages
async def group_message_handler(client: Client, message: Message):
    chat_id = message.chat.id
    game = await db.get_game(chat_id)

    if not game:  # No game is running
        return

    host_id = game.get("host", {}).get("id")
    current_word = game.get("word")

    if message.from_user.id == int(host_id) and message.text:  # Host sent a message
        if current_word and current_word.lower() in message.text.lower():  # Host revealed the answer
            language = await db.get_chat_language(chat_id)
            await message.reply_sticker("CAACAgEAAx0CdytmQADK4wABb7Jj6h5w-f9p5l7k8l4AAj8MAAL58lVDKF-qY-F5j7AeBA")  # Replace with YOUR sticker ID
            await message.reply_text(await get_message(language, "dont_tell_answer"))

    elif message.from_user.id != int(host_id) and current_word and message.text:  # Other user sent a message
        if current_word.lower() == message.text.lower():  # Correct guess
            language = await db.get_chat_language(chat_id)
            winner_id = message.from_user.id
            winner_name = message.from_user.first_name

            await message.reply_text(await get_message(language, "correct_answer", winner=winner_name))

            # Start a new game with the winner as the host
            new_word = choice(game.get("game_mode"))
            new_game_data = {
                'start': time(),
                'host': {'id': str(winner_id), 'first_name': winner_name, 'username': message.from_user.username}, #Added username
                'word': new_word,
                'game_mode': game.get("game_mode")
            }
            try:
                await db.set_game(chat_id, new_game_data)
            except Exception as e:
                logging.error(f"Error setting game in database: {e}")
                await message.reply_text(await get_message(language, "database_error"))
                return

            new_game_message = await get_message(language, "new_game_started")
            await message.reply_text(new_game_message)

            # Notify the previous host (optional)
            try:
                host_user = await client.get_users(int(host_id))
                await client.send_message(int(host_id), await get_message(language, "game_ended_confirmation"))
            except Exception as e:
                logging.error(f"Error notifying previous host {host_id}: {e}")
                
@Client.on_callback_query(filters.regex("view|next|end_game"))
async def game_action_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()  # Acknowledge the callback

    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    language = await db.get_chat_language(chat_id)

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
        word = game['word']
        await callback_query.message.edit_text(await get_message(language, "current_word", word=word), reply_markup=inline_keyboard_markup)

    elif callback_query.data == "next":
        try:
            new_word = choice(game['game_mode'])
            result = await db.update_game(chat_id, {"$set": {"word": new_word}})  # Use chat_id directly
            if result.modified_count == 1:
                await callback_query.message.edit_text(await get_message(language, "new_word", word=new_word), reply_markup=inline_keyboard_markup)
            else:
                logging.error(f"Failed to update word (modified_count: {result.modified_count}) for chat {chat_id}")
                await callback_query.answer(await get_message(language, "word_not_updated"), show_alert=True)
        except Exception as e:
            logging.error(f"Error updating word in database: {e}")
            await callback_query.answer(await get_message(language, "database_error"), show_alert=True)
            return

    elif callback_query.data == "end_game":
        if user_id == host_id:
            await handle_end_game(client, callback_query.message, language)
            await callback_query.message.delete()  # or edit_text with a "game ended" message
            await client.send_message(chat_id, await get_message(language, "game_ended"))  # Send a separate message
            await callback_query.answer(await get_message(language, "game_ended_confirmation"), show_alert=True)

@Client.on_message(filters.group & filters.command("set_mode", CMD))
async def set_game_mode(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    language = await db.get_chat_language(chat_id)

    if not await is_user_admin(client, chat_id, user_id):  # Pass chat_id directly
        await message.reply_text(await get_message(language, "not_admin"))
        return

    mode = message.command[1] if len(message.command) > 1 else None
    if mode not in ["easy", "hard", "adult"]:
        await message.reply_text(await get_message(language, "invalid_mode"))
        return

    try:
        await db.set_group_game_mode(chat_id, mode)  # Use chat_id directly
        await message.reply_text(await get_message(language, "game_mode_set", mode=mode))
    except Exception as e:
        logging.error(f"Error setting game mode in database: {e}")
        await message.reply_text(await get_message(language, "database_error"))
        return

async def handle_end_game(client: Client, message: Message, language_str: str):  # Language as string
    try:
        language = Language(language_str)  # Convert to enum
    except ValueError:
        language = Language.EN  # Default to EN

    try:
        await db.remove_game(message.chat.id)
        await message.reply_text(await get_message(language, "game_ended"))  # Inform users the game has ended (pass enum)
    except Exception as e:
        logging.error(f"Error removing game from database: {e}")
        await message.reply_text(await get_message(language, "database_error"))  # Inform users of the error (pass enum)
        return  # Important: Exit the function after handling the error
