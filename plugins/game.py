#game.py

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

  
async def new_game(client: Client, message: Message, language: Language, game_mode: str) -> bool:
    try:
        # Ensure game_mode is a string; if it's a list, take the first element
        if isinstance(game_mode, list):
            game_mode = game_mode[0]  # or handle it according to your logic

        # Get a word based on the game mode
        word = choice(game_mode)  
        logging.info(f"Selected word for game mode '{game_mode}': {word}")

        bot_info = await client.get_me()
        bot_id = bot_info.id

        host_id = message.from_user.id
        if host_id == bot_id:
            logging.warning("The bot cannot be the host of the game.")
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

        # Store the game data in the database
        await db.set_game(message.chat.id, game_data)

        # Send a message to the chat indicating the game has started
        await message.reply_text(
            await get_message(language.value, "game_started", name=message.from_user.first_name, mode=game_mode, lang=language.value),
            reply_markup=inline_keyboard_markup  # Ensure this is defined elsewhere
        )
        return True
    except Exception as e:
        logging.error(f"Error in new_game: {e}")
        await message.reply_text(await get_message(language.value, "database_error"))
        return False

async def check_answer(client: Client, message: Message, game: dict, language: Language):
    current_word = game.get("word")
    host_id = game.get("host", {}).get("id")
    chat_id = message.chat.id  # Get the chat ID
    user_id = message.from_user.id  # Get the user ID

    if message.text:  # Check if the message is a text message
        if message.text.lower() == current_word.lower():  # Direct comparison
            winner_id = message.from_user.id
            winner_name = message.from_user.first_name

            if winner_id == int(host_id):  # Host provided the answer
                await message.reply_sticker("CAACAgUAAyEFAASMPZdPAAEBWjVnnj1fEKVElmmYXzBc828kgDZTQQACNBQAAu9OkFSKgGFg2iVa2R4E")
                await message.reply_text(await get_message(language, "dont_tell_answer"))  # Use the text from your script
            else:  # Non-host provided the answer
                await handle_end_game(client, message, language)  # End the current game
                
                # Update the user's score, coins, and XP
                await update_user_score(chat_id, user_id, base_score=10, coins=5, xp=20)
                
                await message.reply_text(
                    await get_message(language, "correct_answer", winner=winner_name)  # Use the correct answer text
                )
                
                await new_game(client, message, language, game.get("game_mode"))  # Start a new game
                # The new_game function will handle sending the "game started" message

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
        
        # Check if the game has timed out
        if time_elapsed >= GAME_TIMEOUT:
            await handle_end_game(client, message, language)  # End the ongoing game
            game_mode = await db.get_group_game_mode(chat_id)  # Get the game mode
            await new_game(client, message, language, game_mode)  # Start a new game
            return

        # If the game is still ongoing, check if the user is the host
        host_id = ongoing_game["host"]["id"]
        if message.from_user.id != host_id:
            await message.reply_text(await get_message(language, "game_already_started"))
            return

    # If no ongoing game or the user is the host, start a new game
    game_mode = await db.get_group_game_mode(chat_id)  # Get the game mode
    await new_game(client, message, language, game_mode)  # Start a new game
    await message.reply_text(await get_message(language, "new_game_started"))  # Inform the user that a new game has started

@Client.on_message(filters.group)
async def group_message_handler(client: Client, message: Message):
    chat_id = message.chat.id
    language_str = await db.get_chat_language(chat_id)
    
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN
        logging.warning(f"Invalid language string '{language_str}' in database for chat {chat_id}. Defaulting to EN.")

    # Retrieve the current game state
    game = await db.get_game(chat_id)

    if not game:
        return  # No game ongoing, exit the function

    # Call the check_answer function to handle answer checking
    await check_answer(client, message, game, language)

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
            if isinstance(game_mode, list) and game_mode:
                game_mode = game_mode[0]  # Use the first mode if it's a list
            else:
                logging.warning(f"No valid game mode found for chat_id: {chat_id}. Defaulting to 'easy'.")
                game_mode = "easy"  # Default to "easy" if no valid mode is found
                
            new_word = choice(game_mode)  # Use the string for choice()
            update_data = {"word": new_word}  # Prepare the update data
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

@Client.on_callback_query(filters.regex("choose_leader"))
async def choose_leader_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Get the language for the chat
    language_str = await db.get_chat_language(chat_id)
    try:
        language = Language(language_str)
    except ValueError:
        language = Language.EN

    # Get the game mode for the new game
    try:
        game_mode = await db.get_group_game_mode(chat_id)  # Get the game mode
        if not game_mode:
            logging.warning(f"No game mode found for chat {chat_id}. Defaulting to 'Easy'.")
            game_mode = "easy"  # Default game mode if none is found
    except Exception as e:
        logging.error(f"Error retrieving game mode for chat {chat_id}: {e}")
        await callback_query.answer("Failed to retrieve game mode. Please try again.", show_alert=True)
        return

    # Start a new game with the user who clicked the button as the leader
    try:
        await new_game(client, chat_id, user_id, language, game_mode)  # Pass necessary parameters
        await callback_query.answer(f"{callback_query.from_user.first_name} is now the leader! Starting the game...")
    except Exception as e:
        logging.error(f"Error starting new game for chat {chat_id}: {e}")
        await callback_query.answer("Failed to start the game. Please try again.", show_alert=True)

async def handle_end_game(client: Client, message: Message, language: Language):
    try:
        await db.remove_game(message.chat.id)
        
        # Create an inline keyboard with a button to choose a new leader
        inline_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("I Want To Be A Leader 🙋‍♂️", callback_data="choose_leader")]]
        )
        
        # Use get_message to retrieve the translation for "choose_leader"
        await message.reply_text(
            await get_message(language, "choose_leader"),  # Retrieve the message in the correct language
            reply_markup=inline_keyboard
        )
    except Exception as e:
        logging.error(f"Error removing game from database: {e}")
        await message.reply_text(await get_message(language, "database_error"))  # Use enum
